# Server version map

## stable

### v42 — `stub_server_v42_grass_timer_test.py`

Known stable baseline for current farm work.

- `grass_to_start_grow = 300`
- digging works via ACTION 201 + `FarmField.status="digged"`
- seed purchase works
- sowing is client-visible but ACTION 204 is still generic server success
- watering ACTION 203 still needs state persistence
- city ACTION 404 is not implemented

## experiments

### v43 — `stub_server_v43_mow_city_test.py`

Do not use as baseline.

- timer changed to 30 and field flow became unstable
- mower response was speculative
- fixed32 literal bug present
- city/NPC response was speculative

### v44 — `stub_server_v44_mow_isolated_test.py`

Current isolated mower experiment.

- based on stable v42
- timer 300 retained
- mower count/dedup state added
- game does not crash
- mowing currently sends `status="digged"`, which is proven wrong because harvesting should not remove the plant

Next experimental version should implement persistent per-field state before city work resumes.
