# Current protocol findings

Last updated: 2026-08-11

## Confirmed request actions

| ACTION | Meaning | Confirmed request fields | Current status |
|---|---|---|---|
| 1 | Get GameSettings | 1=session_id, 2=local_time, 3=user_action_id | Working |
| 2 | Get UserState | 1=session_id, 2=local_time, 3=user_action_id, 14=type_id | Working |
| 4 | Water-tool preparatory action | 3=user_action_id, 10=hose_id | Partial |
| 5 | Buy seed packet | 3=user_action_id, 4=coordinates, 11=product_id | Working |
| 7 | Enter/transition to city/market | 3=user_action_id, 9=mow_id | Transition only |
| 106 | Periodic service request | 3=user_action_id | Working, meaning unknown |
| 201 | Dig farm field | 3=user_action_id, 7=field_id, 8=spade_id | Working |
| 202 | Mow field | 3=user_action_id, 7=field_id, 9=mow_id | Protocol works, semantics still wrong |
| 203 | Water farm field | 3=user_action_id, 7=field_id, 10=hose_id | Needs stateful response |
| 204 | Sow seed | 3=user_action_id, 7=field_id, 12=seed_packet_id | Not implemented; currently generic success |
| 404 | Request after city entry | 3=user_action_id, 29=flag_id | Not implemented |

## Confirmed FarmField fields

- field 1 = `id`
- field 2 = `water_amount` (`float`, protobuf fixed32 / wire type 5)
- field 6 = `status` (`string`)
- `status="digged"` is accepted by the client and visually produces a dug field.

Strong working hypotheses from schema/tests:

- field 3 = `fertil_amount`
- field 4 = `product_id`
- field 5 = `percent_growth`
- field 7 = `color_id`

## Water

A previous working test proved that returning `FarmField.water_amount = 1.0` works. In v44 ACTION 203 returns only `Response(result=1)`, so the server does not persist or resend water state. This is the likely reason the water indicator resets after later actions.

## Mowing

v44 returns `FarmField(status="digged")` after ACTION 202. This directly explains why mowing currently removes the plant and visually turns the cell into a dug field. Mowing must preserve the planted product/state instead of using `digged`.

The MowMachine response path appears usable: the test counter increased consistently from 1 upward.

## Sow

ACTION 204 is confirmed as:

- request field 7 = `field_id`
- request field 12 = `seed_packet_id`

v44 currently handles it through the generic `result=1` fallback, so the server never records which product is planted on a cell.

## Required next architecture

The server should become stateful per farm cell, e.g.:

```text
farm_fields[field_id] = {
    status,
    water_amount,
    product_id,
    percent_growth,
    fertil_amount,
    color_id,
}
```

Actions 201/202/203/204 should update only their own properties and send a coherent FarmField back to the client.

## Grass timer

`grass_to_start_grow = 300` is the current stable diagnostic value. Testing `30` caused the digging/growth loop to break, so 30 should not be copied from Chudo Ferma 2 without understanding units/semantics.

## City

After ACTION 7 the client sends ACTION 404 with request field 29 = `flag_id`, observed as `0`.

The embedded protobuf schema contains city-related structures including `SingleCityInfo`, `CityMarketList`, `CityCheck`, `CityContracts`, `NPCVoc`, and city vocabulary tables. The earlier v43 `UserList` NPC response was only a speculative experiment and is not considered confirmed.
