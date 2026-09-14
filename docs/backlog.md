# Backlog

> [!NOTE]
> This file was written by Claude and reflects scope decisions made with the user during the build. It is a to-do list, not a plan.

Parked items, roughly in priority order.

Resolved 2026-09-11 (evening): room temperature and live power, via the
selector-write-then-read pattern found in Dimplex's ConfigR app. See
`ble-protocol.md`.

Scope decision 2026-09-11: the ESP32 build covers Manual mode and setpoint
only, plus the read-only room temperature, heating state and power. Everything
below is out of scope until asked for.

- **Bring up the remaining two radiators** (QRAD100E #2, QRAD150E). Office
  QRAD100E done 2026-09-11, living room QRAD200E Series D done 2026-09-14. Dump
  each new one first to confirm series letter and GATT layout.
- **Timer, Boost, Advance, Away writes.** Read side fully decoded in
  `ble-protocol.md`. `tools/ble_set_mode.py boost <min>` is written but untested.
- **Clock sync.** The QRAD100E clock is 22 min slow. 0x0006 (ConfigR: SetRtc,
  write-only, 7 bytes) format [20, YY, MM, DD, hh, mm, dst]; ConfigR's SetRtc
  encoder gives the exact byte layout if the observed one doesn't hold. The
  ESP32 can keep the radiators on NTP time for free.
- **Firmware versions as diagnostics.** 0x2001 with the selector write
  (0 controller, 1 UI, 2 RF) returns [n, major, minor]. Cheap to add.
- **Schedule read/write** via 0x1002 (Sunhouse format, 31 bytes). Only needed
  if timer modes are driven from HA rather than Manual + HA automations.
- **Remaining unnamed characteristics**: 000b, 000c, 1003, 100a, 100b, 100f,
  1012-1015, 1022, 1029, 1050, 2003, 2009, 200b, 200c, 200d, 200f. Everything
  else is named in `ble-protocol.md` from ConfigR.
- **Keep-alive need.** Sunhouse writes the clock every 3 s to hold the
  connection. The ESPHome node polls every 10 s and has held a connection for
  hours; a truly idle link is untested. Only matters if polling is ever reduced.
- **Climate entity.** Currently a number entity; a `generic_thermostat` in HA
  using the room sensor gives a thermostat card. Could also be done on the node
  now that it reads the radiator's own room temperature.
- **RFM slot pinout.** Parked. Only relevant if BLE turns out to have a gap.
