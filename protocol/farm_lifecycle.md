# Farm lifecycle research note

Desired logical lifecycle under current reconstruction:

1. Digging (ACTION 201) changes the field into a dug/plantable state.
2. Sowing (ACTION 204) records which seed/product is planted on that field.
3. Watering (ACTION 203) increases/stores `water_amount` without erasing planted-product or growth state.
4. Growth changes `percent_growth`/status over time.
5. Mowing/harvesting (ACTION 202) collects resource into the mower but must not incorrectly replace the field with `status="digged"` if the crop is intended to remain/regrow.

Current v44 is not yet stateful, so independent responses can overwrite or lose other field properties.
