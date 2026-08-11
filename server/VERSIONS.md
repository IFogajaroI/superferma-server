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

Previous isolated mower experiment.

- based on stable v42
- timer 300 retained
- mower count/dedup state added
- game does not crash
- mowing sends `status="digged"`, proven wrong because harvesting should not remove the plant

### v45 — `stub_server_v45_stateful_fields_test.py`

Current stateful farm-field experiment.

- keeps v44 GameSettings/UserState baseline and `grass_to_start_grow = 300`
- ACTION 201 resets one field to a clean `digged` state
- ACTION 5 remembers which `product_id` belongs to returned `seed_packet_id=1`
- ACTION 204 stores planted `product_id`, sets `status="grow"`, and resets `percent_growth=0`
- ACTION 203 sets `water_amount=1.0` while preserving product/growth/status
- ACTION 202 preserves water/product, keeps `status="grow"`, resets only growth stage, and updates MowMachine product count
- immediate duplicate mower packets are suppressed for one second only
- ACTION 404 remains untouched

Test v45 before promoting any part of it to stable.
