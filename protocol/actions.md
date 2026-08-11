# ACTION quick reference

| ACTION | Request fields | Meaning |
|---|---|---|
| 1 | 1, 2, 3 | GameSettings |
| 2 | 1, 2, 3, 14 | UserState |
| 4 | 3, 10 | Water-tool action |
| 5 | 3, 4, 11 | Buy seed packet |
| 7 | 3, 9 | Enter/transition to city/market |
| 106 | 3 | Periodic service request |
| 201 | 3, 7, 8 | Dig field |
| 202 | 3, 7, 9 | Mow field |
| 203 | 3, 7, 10 | Water field |
| 204 | 3, 7, 12 | Sow seed |
| 404 | 3, 29 | Post-city-entry request (`field29 = flag_id`) |

Common request fields currently confirmed:

- field 3 = `user_action_id`
- field 7 = `field_id`
- field 8 = `spade_id`
- field 9 = `mow_id`
- field 10 = `hose_id`
- field 11 = `product_id`
- field 12 = `seed_packet_id`
- field 29 = `flag_id`

See `current_findings.md` for details and confidence notes.
