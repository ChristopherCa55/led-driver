# Reference files (frozen 2026-10-05, do not edit)

| Folder | What | BOOST.asc sha256 |
|---|---|---|
| `LTspice_original/` | The electrical source of truth: a copy of `led-driver/BOOST_stuff/LTspice/` (BOOST.asc + 23 .asy/.lib files) | `6492c5d092822bbba10f3a868af3b510697d3689b7f43f731ac282f05a47b16a` |
| `reorg_2026-10-05_attempt/` | The failed earlier re-layout, from `led-driver/BOOST_reorg_2026-10-05/LTspice/`, with the same support files. **An example of what not to do** (README §2) | `be145b76f32b409f48e98c380fbcbc66529c2cb05f5f430bedc05e95a63488d6` |

`tools/ltspice_equiv.py` compares against `LTspice_original/` by default.
