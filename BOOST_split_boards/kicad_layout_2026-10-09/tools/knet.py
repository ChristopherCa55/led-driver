"""Read a KiCad XML netlist: components and nets."""
import xml.etree.ElementTree as ET


def read(path):
    r = ET.parse(path).getroot()
    comps = {}
    for c in r.find('components'):
        ref = c.get('ref')
        comps[ref] = {'value': (c.findtext('value') or ''), 'footprint': c.findtext('footprint') or '',
                      'lib': (c.find('libsource').get('lib') + ':' + c.find('libsource').get('part'))
                      if c.find('libsource') is not None else ''}
    nets = {}
    for n in r.find('nets'):
        nets[n.get('name')] = [(nd.get('ref'), nd.get('pin'), nd.get('pinfunction') or '', nd.get('pintype') or '')
                               for nd in n.findall('node')]
    return comps, nets


if __name__ == '__main__':
    import sys
    comps, nets = read(sys.argv[1])
    print(len(comps), 'components', len(nets), 'nets')
