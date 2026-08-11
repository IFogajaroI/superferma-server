# City research note

Confirmed so far:

- ACTION 7 transitions toward city/market flow without crashing.
- After ACTION 7, the client sends ACTION 404.
- ACTION 404 request includes field 29 = `flag_id`, observed as 0.
- The earlier v43 response using `UserList` with two guessed NPC farms was speculative and is not a confirmed schema for ACTION 404.
- Embedded schemas expose city/NPC structures such as `NPCVoc`, `SingleCityInfo`, `CityMarketList`, `CityCheck`, and `CityContracts`.

Do not mix city experiments into farm-state fixes until ACTION 201/202/203/204 lifecycle is stable.
