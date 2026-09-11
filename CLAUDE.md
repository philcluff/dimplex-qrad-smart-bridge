# CLAUDE.md

Guidance for agents working in this repo. Read `README.md` first for the user-facing story.

## What this is

ESPHome firmware for one ESP32-S3 per Dimplex Q-Rad E radiator, controlling the radiator over its built-in BLE from Home Assistant, plus the reverse-engineering notes and tools that got there. Scope is deliberately Manual mode and target temperature only. The Dimplex Hub, RFM module and cloud are not used and not emulated.

## Layout

- `esphome/qrad-common.yaml` - the ESPHome package; this is the product
- `esphome/qrad-<room>.yaml` - one per radiator: name, friendly name, BLE MAC
- `esphome/secrets.yaml` - Wi-Fi, API key, OTA and fallback-AP passwords; gitignored, never commit or paste its contents. `secrets.yaml.example` is the template
- `esphome/README.md` - entities, bring-up steps per radiator, REST routes, bring-up lessons
- `docs/ble-protocol.md` - the GATT table with every characteristic marked confirmed / inferred / unknown, plus raw capture sessions. Update it whenever a characteristic's meaning is learned or a write format is proven
- `docs/research.md` - the Dimplex ecosystem, why BLE and not RF or the slot, prior art, sources
- `docs/backlog.md` - parked work; the scope decision lives at the top
- `tools/*.py` - bleak scripts for a Mac: dump, watch, scan, and write tests that restore state
- `captures/*.json` - raw GATT dumps, one per radiator per occasion
- `mise.toml` - Python 3.13, `.venv`, and tasks for the tools and ESPHome
- `requirements.txt` - pins ESPHome; bleak comes from ESPHome's own pin
- `.github/workflows/build.yml` - CI validates and compiles the office config with placeholder secrets

## Build and run

Everything runs through mise from the repo root so `.venv` and `esphome/secrets.yaml` are found:

```
mise run deps                                                   # install pinned deps into .venv
mise run esphome-config esphome/qrad-office.yaml                # validate
mise exec -- esphome compile esphome/qrad-office.yaml           # build without flashing
mise run esphome-run esphome/qrad-office.yaml --device qrad-office.local   # OTA flash the live node
mise run esphome-logs esphome/qrad-office.yaml --device qrad-office.local  # stream logs
mise run watch                                                  # diff readable characteristics live
```

Build output goes to `esphome/.esphome/`, gitignored. Always validate before declaring a config change done. The nodes are in daily use, so only flash when the user asks. Never run the write-test tools or write to the radiator without the user saying so.

There are no tests.

## Design decisions to preserve

- **Target Temperature reports truth, not intent.** The number is non-optimistic; it publishes what `0x1023` reads back, 30 s polls plus a re-read one second after each write, and goes unavailable when disconnected. Don't make it optimistic or seed it with a default.
- **Setpoint writes go to the manual family.** If `0x1001` byte 0 is not 2 or 3, write Manual first, wait 300 ms, then the setpoint. Otherwise a write in Timer only edits the current period. Mode 2 versus 3 is decided by the radiator from the setpoint (19 and below Eco, 20 and above Manual), not by us.
- **Encryption is requested explicitly on connect.** On ESP-IDF, `esp_ble_set_encryption()` after service discovery is what triggers pairing; without it every read fails with GATT status 15 and no passkey prompt appears. Keep it in `on_connect`.
- **Passkey entry is a text entity that clears itself.** Six digits, validated, replied via `ble_client.passkey_reply`, then blanked. Don't store it.
- **Refreshes come from the main loop.** The mode read publishes the Mode text directly, and the 2 s interval requests a mode read whenever connected with no mode known. Don't chain delayed actions off BLE triggers.
- **Never write to** the two Cypress bootloader services (`00060000-f8ce-...`) or the property-less characteristics `2006`-`2008` and `200f`. `docs/ble-protocol.md` lists what is safe.
- **LED semantics are fixed:** green connected, amber not. Channel order on the S3-Zero is RGB, brightness 0.5, pin from the `led_pin` substitution. Documented in both READMEs; change both or neither.
- **One node, one radiator.** BLE through walls is poor and the radiator accepts one central. Don't try to multiplex.

## Attribution

The BLE service, characteristic numbering and the ESPHome config skeleton come from JYewman's Sunhouse project (linked in the README credits and at the top of `qrad-common.yaml`). Keep that attribution when refactoring, and credit any further upstream source the same way when it contributes something.

## Conventions

- Keep the shared config in one package file; per-radiator files carry substitutions only.
- Prefer self-documenting config and code over comments.
- When a characteristic's meaning changes status (unknown to inferred to confirmed), update `docs/ble-protocol.md` in the same change, with the date and how it was shown.
- Update the README LED or entity tables if pins or behaviour change.
- Radiator BLE MACs in the per-room configs are fine to commit; passkeys and `secrets.yaml` are not.
- Never commit on the author's behalf.
- Never search or scan outside this repo for files; ask where things are.
