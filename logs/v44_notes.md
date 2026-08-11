# v44 log notes

Source runtime log SHA-256: `4c4302ee63cc27920be4e360e18e69ea13dbc54f336a51b812c8ea0f5d7210dc`.

Important observations from the 2026-08-11 v44 run:

- ACTION 203 repeatedly arrives as request field 7 = farm field ID and field 10 = hose ID.
- v44 replies to ACTION 203 with only `Response(result=1)`, so water state is not persisted in the server response.
- ACTION 204 repeatedly arrives as request field 7 = farm field ID and field 12 = seed packet ID.
- v44 sends ACTION 204 through the generic success fallback, so planted-product state is not persisted server-side.
- ACTION 202 arrives as field 7 = field ID and field 9 = mower ID 2.
- v44 mower grass count advanced consistently (1, 2, 3, ...), indicating the MowMachine response path is at least accepted by the client.
- v44 also returns `FarmField.status="digged"` after mowing; the game visibly removes the plant/turns the cell into a dug field, proving this status is wrong for harvesting.
- The game remained stable with `grass_to_start_grow = 300`.

The full raw log should be uploaded later using the exact filename/hash from `server/FILE_MANIFEST.md`.
