# Backlog

> [!NOTE]
> This file was written by Claude and reflects scope decisions made with the user during the build. It is a to-do list, not a plan.

Parked items, roughly in priority order.

Scope decision 2026-09-11: the ESP32 build covers Manual mode and setpoint
only. Everything below is out of scope until asked for.

- **Timer, Boost, Advance, Away writes.** Read side fully decoded in
  `ble-protocol.md`. `tools/ble_set_mode.py boost <min>` is written but untested.

- **Room temperature over BLE.** Not in any readable characteristic, no notify path, debug menu changes nothing. Likely a write-then-read request. Needs the ConfigR APK (`com.Dimplex.DimplexToolkit`) decompiled with jadx; scripted mirror downloads are blocked, so pull it from an Android device or download manually. Not blocking: every room already has a sensor, and the ESP32 can carry one.
- **Bring up the other three radiators** (QRAD100E #2, QRAD150E, QRAD200E). Boards ordered. Dump each first to confirm series letter and identical GATT layout; note whether the `AL9502` name prefix differs per unit.
- **Clock sync.** The QRAD100E clock is 22 min slow. 0x0006 is writable, format [20, YY, MM, DD, hh, mm, dst]. Sunhouse writes it as a keep-alive; the ESP32 can keep the radiators on NTP time for free. Test the write, and check whether the last byte is DST or day-of-week.
- **Schedule read/write** via 0x1002 (Sunhouse format, 31 bytes). Only needed if timer modes are driven from HA rather than Manual + HA automations.
- **Unknown characteristics**: 1005, 1007, 1008, 1011, 1012-1015, 1016, 1017, 100a-100f, 1019, 1020, 1022, 2001, 2003, and the 000b/000c int8 tables. Settings toggles (sound, adaptive start, open window detection, units, locks) are probably among 100a-100f. Enumerate by toggling each in Settings while watching.
- **Keep-alive need.** Sunhouse writes the clock every 3 s to hold the connection. The ESPHome node polls every 10 s and has held a connection for hours; a truly idle link is untested. Only matters if polling is ever reduced.
- **Climate entity.** Currently a number entity; a `generic_thermostat` in HA using the room sensor gives a thermostat card. Could also be done on the node with a `homeassistant` sensor import.
- **RFM slot pinout.** Parked. Only relevant if BLE turns out to have a gap.
