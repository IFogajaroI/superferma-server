# State model draft

Planned server-side farm state:

```python
farm_fields[field_id] = {
    "status": ...,
    "water_amount": ...,
    "fertil_amount": ...,
    "product_id": ...,
    "percent_growth": ...,
    "color_id": ...,
}
```

This is a design note, not yet implemented in the stable server.
