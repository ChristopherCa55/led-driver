// Complete the 0603 candidate's JLC CSVs without changing the working copy.
// Usage: bundled-node step05g_fab.mjs preview|build
// Artifact Tool edits the tabular values; serialization preserves the source CSV convention.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
// The workspace sandbox rejected a node_modules junction; resolve the bundled public entry instead.
const bundledRequire = createRequire('C:/Users/bubba/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {Workbook} = await import(pathToFileURL(bundledRequire.resolve('@oai/artifact-tool')).href);

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../../');
const copy = path.join(root, 'BOOST_review_fixes');
const pcb = path.resolve(here, '../step05g/kicad/BOOST_control_RC2.kicad_pcb');
const mode = process.argv[2];
assert(['preview', 'build'].includes(mode));
const out = path.join(here, mode === 'preview' ? 'csv_before' : 'fab');
await fs.mkdir(out); // Refuse to overwrite a previous run.
const sha = b => createHash('sha256').update(b).digest('hex');
const pcbBytes = await fs.readFile(pcb);
assert.equal(sha(pcbBytes), '82b638b606ea6e1e294ea37d4ad58e6a0340da94dd3be8194e5f616207866fb0');
const pcbText = pcbBytes.toString('utf8').replaceAll('\r\n', '\n');
const manifests = [];

function serialize(row) {
  return row.map(v => {
    const t = String(v ?? '');
    return /[",\r\n]/.test(t) ? '"' + t.replaceAll('"', '""') + '"' : t;
  }).join(',');
}
function placement(ref) {
  const pos = pcbText.indexOf(`(property "Reference" "${ref}"`);
  assert(pos >= 0);
  const block = pcbText.slice(pcbText.lastIndexOf('\n\t(footprint ', pos), pos);
  assert(block.includes('Resistor_SMD:R_0603_1608Metric'));
  const at = block.match(/\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)/);
  assert(at);
  assert(block.includes('(layer "F.Cu")'));
  return [ref, Number(at[1]).toFixed(4) + 'mm', (-Number(at[2])).toFixed(4) + 'mm', 'Top', String(Number(at[3] ?? 0))];
}

for (const kind of ['BOM', 'CPL']) {
  const filename = `BOOST_control_${kind}_JLC.csv`;
  const source = await fs.readFile(path.join(copy, filename));
  const text = source.toString('utf8');
  const newline = text.includes('\r\n') ? '\r\n' : '\n';
  const trailing = text.endsWith(newline);
  const rawLines = text.split(newline);
  if (trailing) rawLines.pop();
  const wb = await Workbook.fromCSV(text, {sheetName: kind});
  const sh = wb.worksheets.getItem(kind);
  const rows = sh.getUsedRange().values;
  assert.equal(rows.length, rawLines.length);
  // Require a byte-identical round trip before editing; preserve every unrelated row.
  assert.equal(rows.map(serialize).join(newline) + (trailing ? newline : ''), text);
  const original = structuredClone(rows);
  const changed = [];
  let previewRange;
  if (kind === 'BOM') {
    for (const [code, remove, add] of [
      ['C25804', ['R99','R102'], []],
      ['C21190', [], ['R99','R102']],
      ['C23162', [], ['R106','R107']],
    ]) {
      const indexes = rows.map((r,i) => r[3] === code ? i : -1).filter(i => i >= 0);
      assert.equal(indexes.length, 1);
      const i = indexes[0];
      const refs = rows[i][1].split(',');
      for (const r of remove) assert(refs.includes(r));
      for (const r of add) assert(!refs.includes(r));
      if (mode === 'build') {
        const final = refs.filter(r => !remove.includes(r)).concat(add).sort((a,b) => Number(a.slice(1))-Number(b.slice(1)));
        sh.getRange(`B${i+1}`).values = [[final.join(',')]];
      }
      changed.push(i);
    }
    previewRange = `A${Math.min(...changed)+1}:D${Math.max(...changed)+1}`;
  } else {
    const i = rows.findIndex(r => r[0] === 'R105');
    assert(i > 0);
    assert(!rows.some(r => ['R106','R107'].includes(r[0])));
    const additions = ['R106','R107'].map(placement);
    if (mode === 'build') sh.getRange('A1').write([...rows.slice(0,i+1), ...additions, ...rows.slice(i+1)]);
    previewRange = `A${i-4}:E${i+(mode === 'build' ? 3 : 1)}`;
    changed.push(i+1,i+2);
  }
  wb.recalculate();
  const finalRows = sh.getUsedRange().values;
  if (mode === 'build') {
    if (kind === 'BOM') {
      assert.equal(finalRows.length, original.length);
      for (let i=0;i<original.length;i++) {
        if (!changed.includes(i)) assert.deepEqual(finalRows[i],original[i]);
        else for (const c of [0,2,3]) assert.equal(finalRows[i][c],original[i][c]);
      }
      const allRefs = finalRows.slice(1).flatMap(r=>r[1].split(','));
      assert.equal(new Set(allRefs).size,allRefs.length);
      for (const [r,code] of [['R99','C21190'],['R102','C21190'],['R106','C23162'],['R107','C23162']]) {
        const row = finalRows.find(a=>a[1].split(',').includes(r));
        assert.equal(row[3],code); assert.equal(row[2],'0603');
      }
    } else {
      assert.deepEqual(finalRows.filter(r=>!['R106','R107'].includes(r[0])),original);
      assert.equal(finalRows.length,original.length+2);
    }
    const outputText = finalRows.map(serialize).join(newline)+(trailing?newline:'');
    await fs.writeFile(path.join(out,filename),outputText,{flag:'wx'});
    const check = await Workbook.fromCSV(outputText,{sheetName:'Check'});
    assert.deepEqual(check.worksheets.getItem('Check').getUsedRange().values,finalRows);
    manifests.push({file:filename,sourceSHA256:sha(source),outputSHA256:sha(Buffer.from(outputText)),lineEnding:newline==='\r\n'?'CRLF':'LF',rowsBefore:original.length-1,rowsAfter:finalRows.length-1,changes:changed.map(i=>({row:i+1,values:finalRows[i]}))});
    console.log(kind, JSON.stringify(manifests.at(-1)));
  }
  // CSVs have no stored visual formatting; these formats apply to QA previews only.
  sh.getUsedRange().format.font = {name:'Arial',size:11};
  if (kind === 'BOM') sh.getRange('C1:C250').setNumberFormat('@');
  sh.getRange('A1:A250').format.columnWidthPx = kind === 'BOM' ? 220 : 110;
  sh.getRange('B1:B250').format.columnWidthPx = kind === 'BOM' ? 650 : 145;
  sh.getRange('C1:C250').format.columnWidthPx = 145;
  sh.getRange('D1:E250').format.columnWidthPx = 110;
  const preview = await wb.render({sheetName:kind,range:previewRange,scale:1.5,format:'png'});
  await fs.writeFile(path.join(out,`${kind.toLowerCase()}_${mode}.png`),new Uint8Array(await preview.arrayBuffer()),{flag:'wx'});
}
if(mode==='build') await fs.writeFile(path.join(out,'CHECKS.json'),JSON.stringify({candidatePCB:pcb,pcbSHA256:sha(pcbBytes),status:'PASS',files:manifests},null,2)+'\n',{flag:'wx'});
