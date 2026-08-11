# Development workflow

This repository is used to reconstruct the local server behaviour for Superferma 2.29.

## Branch/file discipline

- `server/stable/` contains only known-working baselines.
- `server/experiments/` contains diagnostic builds and hypotheses.
- `protocol/` contains protobuf field maps, ACTION notes, and extracted protocol knowledge.
- `logs/` contains selected runtime traces that prove client/server behaviour.
- `docs/` contains research notes and process documentation.

## Testing rule

Before changing a script, first state:

1. what the previous test proved;
2. what exact hypothesis is being tested;
3. what code will change;
4. what must remain untouched;
5. what result should be observed in the game and logs.

Only then create the next experimental version.

## Current next target

The next server version should focus on a stateful farm-field model before returning to city/NPC work.

Priority order:

1. persist `FarmField.water_amount` after ACTION 203;
2. implement ACTION 204 so the server records the planted product;
3. make ACTION 202 harvest into the mower without returning `status="digged"`;
4. preserve all unrelated field properties when one action changes;
5. only after the farm loop is stable, investigate ACTION 404 and the two farmer-bot shops.

## Safety baseline

`grass_to_start_grow = 300` remains the stable diagnostic timer until its units/meaning are proven. Do not reintroduce 30 in an unrelated test.
