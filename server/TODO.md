# TODO

## Farm state

- Implement persistent `farm_fields[field_id]` state.
- ACTION 203: persist and return `water_amount`.
- ACTION 204: persist planted product/seed state.
- ACTION 202: harvest resource without turning the cell into `digged`.
- Preserve unrelated FarmField properties across all actions.

## City

- Keep city changes isolated until farm lifecycle is stable.
- Decode the real ACTION 404 response.
- Restore the two farmer-bot shops using confirmed NPC/city protobuf structures.

## Raw repository artifacts

Upload exact files listed in `server/FILE_MANIFEST.md` and verify SHA-256 values.
