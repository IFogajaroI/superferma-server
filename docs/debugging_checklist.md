# Debugging checklist

For every new server experiment:

- Restart `game.exe` before testing.
- Record server version and exact hypothesis.
- Confirm ACTION 1/2 startup first.
- Test one gameplay path only.
- Capture the runtime log.
- Record visible game behaviour.
- Compare request/response protobuf fields with the previous stable version.
- Do not promote an experiment to stable until user confirms it.
