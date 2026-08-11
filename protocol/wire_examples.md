# Known protobuf wire examples

- `(7, 0, 23)` = Request field 7, varint, value 23 => `field_id=23`.
- `15 0000803f` in a FarmField payload = field 2, wire type 5, float 1.0 => `water_amount=1.0`.
- `32 06 646967676564` = FarmField field 6, string length 6, value `digged`.

Normal server response transport currently used by the local server:

```text
2-byte little-endian frame length
00                      # normal response route/opcode byte
protobuf body
```

The frame length includes the leading `00` response byte.
