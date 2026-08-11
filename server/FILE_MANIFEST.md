# Working file manifest

Last updated: 2026-08-11

These are the exact local files used during the current reverse-engineering session. SHA-256 values are recorded so uploaded copies can be verified later.

| Target repository path | Local source | SHA-256 | Role |
|---|---|---|---|
| `server/stable/stub_server_v42_grass_timer_test.py` | `stub_server_v42_grass_timer_test(1).py` | `c9a4eeb4eafd2e421ec42a676df2be85de4e6b94b424a3bd7ef1dcff6af44db0` | Last stable baseline before mower/city experiments |
| `server/experiments/stub_server_v43_mow_city_test.py` | `stub_server_v43_mow_city_test(2).py` | `8f59039746184bab2e07001f76fcfcef50fda9482bddf210037f6348c0a30d82` | Broken experiment: timer 30 + speculative mower/city handling |
| `server/experiments/stub_server_v44_mow_isolated_test.py` | `stub_server_v44_mow_isolated_test.py` | `0125d449ec18ad3ac250f77dede16b60d8282fe227ab786d76c09531a3397f08` | Current isolated mower experiment |
| `logs/superferma_v44_mow_isolated_test.log` | runtime log uploaded 2026-08-11 | `4c4302ee63cc27920be4e360e18e69ea13dbc54f336a51b812c8ea0f5d7210dc` | Real ACTION trace for v44 |
| `protocol/superferma_protocol_map.xlsx` | `superferma_protocol_map.xlsx` | `17d2bd8659a1595bdd53adc8c243fae91ed2344cafde41cb02ed822412a83735` | Protocol/action/field reference workbook |

## Version notes

### v42 — stable baseline

- `grass_to_start_grow = 300`
- ACTION 201 returns `FarmField.status="digged"`
- ACTION 202 only generic success
- ACTION 203 only generic success
- ACTION 204 falls through generic success
- ACTION 7 returns success
- No speculative ACTION 404 implementation

### v43 — do not use as baseline

- Changed grass timer to 30, which caused unstable/looping field behaviour
- Added speculative mower response
- Contained an invalid fixed32 literal in the mower code (`b"\\x00..."` instead of real four zero bytes)
- Added speculative city/NPC response

### v44 — current test build

- Built from v42 with timer 300 preserved
- Isolated ACTION 202 mower handling
- Tracks mowed field IDs and grass count
- Uses `status="digged"` after mowing, which is now proven semantically wrong because mowing should harvest without removing the plant
- Game remains stable; seed sowing works client-side

## Rule for future development

Do not overwrite the stable baseline. New tests should go under `server/experiments/` with a new version number. Promote a version to `server/stable/` only after the user confirms the gameplay flow works.
