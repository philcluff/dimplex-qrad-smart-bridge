# Q-Rad E BLE protocol

> [!NOTE]
> This file was written by Claude during the reverse engineering, from live GATT dumps and watch sessions on a QRAD100E, with the user pressing the radiator's buttons and reporting what the screen showed. Every row marked confirmed was observed on the real radiator; inferred rows lean on the Sunhouse project and haven't been checked here. Treat it as working notes rather than a spec.

Captured 2026-09-11 from a QRAD100E, Series D, firmware identifiers below.
Raw dump: `captures/qrad100e-seriesD-gatt-2026-09-11.json`.

Status key: **confirmed** = observed on the Q-Rad. **inferred** = from
[JYewman's Sunhouse project](https://github.com/JYewman/Sunhouse-Dimplex-Storage-Heater-ESPHome-Home-Assistant),
which reversed this service from the Dimplex Remo app, not yet verified here.
**unknown** = no idea yet. The service UUID and every characteristic number
below that has a Sunhouse meaning were their discovery; the Q-Rad-specific
decoding is from the capture sessions at the bottom of this file.

## Connection

- Advertised name: `AL9502<Dimplex>`. Prefix probably per-unit (check against
  GDID label). No advertised service UUIDs, no manufacturer data.
- Enable via Menu > Settings > Comms > Bluetooth on the radiator.
- Pairing: passkey display, six digits on the radiator screen. Bond persists.
  ESP32 needs `io_capability: keyboard_only` and `ESP_LE_AUTH_REQ_SC_MITM_BOND`,
  as in the Sunhouse config.
- One central at a time.
- Advertising persists indefinitely while Comms > Bluetooth is enabled. Confirmed 10 min after last disconnect, ~2 adverts/s (2026-09-11).
- Bluetooth setting survives a power cut. Radiator switched off at the wall, back on, advertising again within a minute (2026-09-11 09:54).
- No Off/Standby mode exists in the Q-Rad menus. Frost Protect (mode 4, 7 °C) is the practical off.
- Bond survives a power cut. After the wall-switch test, `ble_dump.py` connected and read every characteristic with no passkey prompt (2026-09-11 09:55). Capture: `captures/qrad100e-seriesD-gatt-after-reboot.json`.
- Sunhouse writes the clock characteristic every 3 s as a keep-alive. The ESPHome
  node, polling every 10 s, has held its connection for hours with no keep-alive.
  A truly idle connection is untested.
- Advertised name prefix is per unit. Living room `AL5355` matches its MAC
  ending 53:55; office `AL9502` does not match its MAC ending 95:A2, so the
  derivation isn't simply the MAC. Two data points, no rule yet.
- Passkey appears fixed per radiator rather than rolling: the living room unit
  showed the same six digits on every pairing attempt (2026-09-14).

## Services

| Service UUID | Chars | Role |
|---|---|---|
| 00060000-f8ce-11e4-abf4-0002a5d5c51b | 1 | Cypress PSoC OTA bootloader. Do not touch. |
| 00060000-f8ce-11e4-abf4-0002a5d5c51c | 1 | Cypress PSoC OTA bootloader. Do not touch. |
| 00000000-0000-1000-8000-00805f9b34fb | 20 | Main control (Sunhouse "Glen Dimplex service") |
| 00000000-0001-1000-8000-00805f9b34fb | 7 | Identity / misc |
| 00000000-0002-1000-8000-00805f9b34fb | 6 | Settings |
| 00000000-0003-1000-8000-00805f9b34fb | 20 | Device info, calibration, diagnostics |

All characteristic UUIDs are `0000XXXX-0000-1000-8000-00805f9b34fb`; only the
XXXX is listed below. Values are hex as read.

## Main control service (…-0000-…)

| Char | Props | Value | Status | Meaning |
|---|---|---|---|---|
| 0006 | R/W | 14 1a 09 0b 09 0f 01 | confirmed | Clock: [20, YY, MM, DD, hh, mm, flag]. 2026-09-11 09:15, flag probably DST. Minute byte observed ticking. Not the Sunhouse byte order. Two readings both 22 min behind real time, so decode is right and this unit's clock is slow. |
| 1001 | R/W | 03 00 00 00 00 00 | **confirmed** | Operating mode. Byte 0: **1 Timer, 2 Manual, 3 Eco, 4 Frost Protect**. Byte 1 (timer sub-mode, only meaningful when byte 0 = 1): **1 Out All Day, 2 Home All Day, 3 User Timer, 5 Away**. Byte 3 = 01 while Boost is running (Boost presents as mode 2 + flag). Bytes 2, 4, 5 always 0 so far. Sunhouse's 5 boost / 6 standby not seen. **Write confirmed** `[mode, submode, 0, 0, 0, 0]` with response. **Manual and Eco are one family selected by setpoint**: 19 or below reads 3 (Eco), 20 or above reads 2 (Manual). Writing mode 2 sets setpoint 21; writing mode 3 sets 18; they act as presets. |
| 1002 | R/W | 31 x 00 | inferred | Schedule buffer. Write [0, timerMode, day] then read back 31 bytes: hdr(3), 4 periods x [startH,startM,endH,endM,temp,0], 4 tail bytes. Write [1, timerMode, day, ...] to set. |
| 1003 | R/W | 0f 00 | confirmed | Mirrors 1023 on every change. Briefly read 13 while 1023 read 15 once, so possibly the effective target. |
| 1023 | R/W | 0f 00 | **confirmed R+W** | Target temperature for the current mode/period, LE16 whole degrees. Each mode carries its own value (Eco 15, Manual 21, Frost 7, timer periods 21/7). Write `[temp, 0]` with response accepted; 15 to 17 and back, display followed (2026-09-11 10:00). Single-byte form untested since two-byte worked. |
| 1005 | R/W | 00 | unknown | |
| 1006 | R/W | 07 00 1e 00 | confirmed | Setpoint range min 7, max 30 (bytes 0 and 2). |
| 1007 | R/W | 01 00 00 00 00 00 00 00 00 | unknown | |
| 1008 | R/W | 00 | unknown | |
| 100d | R/W | 00 | **confirmed (read)** | Advance flag in timer modes: 1 when Advance engaged, 0 when released. Setpoint in 1023 flips with the period. Not available in Away. Sunhouse also uses it for boost hours; untested here. |
| 1011 | R | 00 | confirmed (ConfigR) | ErrorStatus: fault code id, 0 = none. |
| 1012-1015 | R/W | 10 x 00 each | unknown | Four 10-byte blocks. Candidates: preset timer definitions or lock config. |
| 1016 | R/W | 00 07 | unknown | Contains 7. Setback or frost temperature? |
| 1017 | R/W | 01 7c | unknown | |
| 1027 | R/W | 00 00 | confirmed | Boost countdown. 0 to 30 (0x1e) when boost started, back to 0 on cancel. Units probably minutes. Boost setpoint (23 here) appears in 1023 while boost runs. |
| 1028 | R/W | 15 00 | confirmed (by user) | Default boost target temperature setting, 21. Per-boost override (23) shows in 1023 while boost runs. |
| 102a | R/W | 00 00 01 01 00 00 07 | **confirmed (read)** | Away mode: [active, YY, MM, DD, mm, hh, temp]. Read 01 1a 09 0c 2e 09 07 = active until 2026-09-12 09:46 at 7 °C (radiator clock). Default 'until tomorrow' is now + 24 h. Byte 0 cleared on exit. |

## Identity service (…-0001-…)

| Char | Props | Value | Status | Meaning |
|---|---|---|---|---|
| 0001 | R/W | 02 b9 ff 96 | confirmed | Display backlight colour [02, R, G, B]. Manual says colour tracks selected temperature, deep blue to bright red. Seen b9ff96, ff7878, 00ff00, 87ceeb, 00008c (frost). |
| 0002 | R/W | 00 00 00 | **confirmed** | ConfigR: Trac. Selector: write `[n,0,0]`, read `[n, active]` for element n. Live heating state. |
| 0007 | R | 03 | confirmed | ConfigR: LastKeyPressValue. Last button pressed; changes as you navigate, which is why it looked like a screen index. |
| 0008 | R/W | 00 00 00 | **confirmed** | ConfigR: TemperatureSensor. Selector: write `[n,0,0]`, read `[n, whole, tenths]`. n=1 room temperature. Read 24.5 °C. |
| 100e | R/W | 00 | unknown | |
| 1010 | R/W | 47 "G" | unknown | |
| 1020 | R/W | 00 | unknown | |

## Settings service (…-0002-…)

| Char | Props | Value | Status | Meaning |
|---|---|---|---|---|
| 0005 | R/W | 01 00 00 | unknown | |
| 100a | R/W | 01 | unknown | Boolean. Debug screen shows flags `BT` and `OW` (Bluetooth, Open Window Detection) both set; this is likely one of them. |
| 100b | R/W | 05 | unknown | |
| 100c | R/W | 00 | unknown | |
| 100f | R/W | 00 | unknown | |
| 1019 | R/W | 00 | unknown | |

## Device info service (…-0003-…)

| Char | Props | Value | Status | Meaning |
|---|---|---|---|---|
| 000a | R/W | e8 03 98 08 00 00 00 00 | confirmed | Debug-page parameters G and H: LE16 1000 and 2200, shown as `G 1000` / `H 2200` on the radiator's debug screen. G is almost certainly rated watts. NOT room temperature. |
| 1022 | R/W | 00 | unknown | |
| 1050 | R | f3 10 00 | unknown | |
| 2001 | R/W | 00 00 00 | confirmed (ConfigR) | SwVersion. Selector: write `[n,0,0]`, read `[n, major, minor]`; n = 0 controller, 1 UI, 2 RF. |
| 2002 | R | (6 bytes, per unit) | confirmed | ConfigR: Gdid. The unit's Glen Dimplex ID, shown big-endian on the debug screen under the name prefix. Redacted here. |
| 2003 | R/W | 00 04 00 | unknown | |
| 2004 | R | "<Dimplex>" | confirmed | Advertised name suffix |
| 2005 | R | "QRAD100E;D;" | confirmed | Model;Series; |
| 000b | R/W | fb x9 f9 x4 | unknown | int8 table, -5/-7. Calibration curve? |
| 000c | R/W | f9 x3 f6 x5 f1 x5 | unknown | int8 table, -7/-10/-15. Calibration curve? |
| 2006-2008 | none listed | | unknown | Probably write-only actions. Do not write blind. |
| 2009 | R | 05 | confirmed | RF firmware revision; debug screen shows `RF Rev 005`. |
| 200a | R | "EP4099" | confirmed | Product code |
| 200b | R | e5 26 | unknown | |
| 200c | R | 14 13 03 0f 0f 23 | unknown | Build date/time? |
| 200d | R | "PGPHS600" | confirmed | Board/firmware code |
| 1029 | R | b9 ff 96 | unknown | Same bytes as the default backlight colour in 0001. Default colour or a colour preset. |
| 200f | none listed | | unknown | Probably write-only. Do not write blind. |

## Writes

Confirmed on Q-Rad:

- Target temperature: write `[temp, 0x00]` to 1023 with response. `tools/ble_set_temp.py`.
- Mode: write `[mode, sub, 0, 0, 0, 0]` to 1001 with response. Tested 2 and 3. `tools/ble_set_mode.py`, `tools/ble_manual_eco_test.py`.

### Control recipe for Manual + setpoint (project scope)

1. Read 1001. If byte 0 is not 2 or 3, write `[2,0,0,0,0,0]` first.
2. Write `[temp, 0]` to 1023.
3. Read 1023 to confirm. Mode byte will read 3 for temp <= 19, 2 for >= 20; both mean manual.

## Sunhouse write formats (inferred, not yet tried on Q-Rad)

- Mode: write `[mode, 3, 0, 0, 0, 0]` to 1001.
- Target temperature: write `[temp]` to 1023.
- Boost: write mode 5 to 1001, wait 200 ms, write `[hours]` to 100d.
- Advance: write `[1]` to 100d to engage, `[0]` to cancel.
- Standby: write `[6, 3, 0, 0, 0, 0]` to 1001.
- Read schedule for day d: write `[0, 3, d]` to 1002, wait 500 ms, read 1002.

## Next

1. ~~Run `tools/ble_watch.py` while changing setpoint, mode, boost, advance.~~ Done, sessions 1 and 2.
2. ~~Identify the room temperature characteristic.~~ Done: 0008 with a selector write, from the ConfigR decompile.
   Ruled out so far (2026-09-11): not in any readable characteristic (display debug menu showed 23.4 while 000a still read 2200 and nothing held 234/2340); no CCCD descriptors exist outside the Cypress bootloader so no notify path; opening the debug menu changes nothing over BLE (not even 0007). Remaining theory: write-then-read request like 1002. Needs the ConfigR APK decompiled rather than blind writes.
3. ~~First write: target temperature to 1023, verified on the display.~~ Done.
4. Dump the other three radiators and diff against this one.
5. ~~Build the ESPHome node.~~ Done, see `esphome/`. Everything in the control recipe is implemented as written.

## Radiator debug screens, 2026-09-11

Two pages, reached from the radiator's own menus (photos not committed). Page 1:

```
AL9502
<12 hex digits, the unit's GDID>
BT
OW
UI Rev 018
RF Rev 005
```

Page 2:

```
A 23.7          ambient temperature (not exposed over BLE)
B 15.0 14.5     setpoint and, probably, the heating-off threshold
C 0
D 0 0
E 300
F 0 0
G 1000          = 000a bytes 0-1
H 2200          = 000a bytes 2-3
```

Page 2 again with the setpoint forced to 30 so the element ran (14:33):

```
A 24.4          ambient
B 30.0 28.3     setpoint and an adjusted target
C 100           heat demand, percent
D 0 1           two element flags; Q-Rad is dual-element, one was on
E 300           constant, probably the control cycle in seconds
F 150 300       on-time within the cycle, 150 of 300 s
G 1000  H 2200  unchanged
```

While C read 100, every readable characteristic was re-read from the ESPHome
node: 000a tail words, 1003, 1005, 1008, 1011, 1016, 1017 all unchanged from
idle. Heating state, demand and ambient are not exposed over BLE in any
readable characteristic. Power would be G x duty, if the duty were available.

The 12-digit ID is 2002 byte-reversed, `RF Rev 005` is 2009. `UI Rev 018`
(0x12) has no obvious match in the dump; 1050 (`f3 10 00`) and 200c are the
candidates. Opening these screens changes nothing readable over BLE.

## Parameter names from Dimplex's ConfigR app

Dimplex's ConfigR installer app (`com.Dimplex.DimplexToolkit`, v3.8.0, a .NET
MAUI app) carries a class per characteristic in
its parameter model, one class per characteristic. Decompiled 2026-09-11 for
interoperability; only the resulting facts are recorded here. This is the
authoritative naming. 61
parameters are defined; 33 exist on the Q-Rad E Series D.

Newer GDHV products expose the same parameters under a vendor base UUID,
`0000XXXX-000S-474C-4E44-494D504C4558` (the tail is ASCII `GLNDIMPLEX`), with
the service number in the fourth group. The Q-Rad uses the Bluetooth SIG base.

| Char | Service | Len | R/W | ConfigR name | On Q-Rad D |
|---|---|---|---|---|---|
| 0002 | …-0001-… | 3 | R | Trac | yes |
| 0003 | …-0001-… | 2 | R | Relay | no |
| 0005 | …-0002-… | 3 | RW | Sound | yes |
| 0006 | …-0000-… | 7 | W | SetRtc | yes |
| 0007 | …-0001-… | 1 | R | LastKeyPressValue | yes |
| 0008 | …-0001-… | 3 | R | TemperatureSensor | yes |
| 000a | …-0003-… | 8 | RW | PowerLoading | yes |
| 000e | …-0001-… | 1 | R | OffpeakStatus | no |
| 0106 | …-0000-… | 8 | W | SetRtcWithSeconds | no |
| 1001 | …-0000-… | 6 | RW | HeatingMode | yes |
| 1002 | …-0000-… | 31 | RW | ScheduleAndSetTemperature | yes |
| 1005 | …-0000-… | 1 | RW | TemperatureUnit | yes |
| 1006 | …-0000-… | 4 | RW | SetpointRange | yes |
| 1007 | …-0000-… | 9 | RW | OpenWindowDetection | yes |
| 1008 | …-0000-… | 1 | RW | PreEmptiveHeating | yes |
| 100c | …-0002-… | 1 | RW | RfComms | yes |
| 100d | …-0000-… | 1 | RW | AdvanceHeating | yes |
| 100e | …-0001-… | 1 | RW | OtaEnable | yes |
| 1010 | …-0003-… | 1 | RW | EolTest | yes |
| 1011 | …-0000-… | 1 | R | ErrorStatus | yes |
| 1016 | …-0000-… | 2 | RW | Setback | yes |
| 1017 | …-0000-… | 2 | RW | Runback | yes |
| 1019 | …-0002-… | 1 | RW | SpConfig | yes |
| 101b | …-0003-… | 1 | R | HeaterSize | no |
| 101c | …-0002-… | 16 | RW | ChargeTimes | no |
| 101d | …-0002-… | 1 | RW | SlaveDevice | no |
| 101e | …-0002-… | 1 | RW | AdditionalCharge | no |
| 1020 | …-0001-… | 1 | RW | TestMode | yes |
| 1023 | …-0000-… | 2 | RW | CurrentSetTemperature | yes |
| 1024 | …-0003-… | 4 | RW | HeatDemand | no |
| 1027 | …-0000-… | 2 | RW | RunbackTime | yes |
| 1028 | …-0000-… | 2 | RW | RunbackSetpoint | yes |
| 102a | …-0000-… | 8 | RW | AwayMode | yes |
| 1030 | …-0002-… | 1 | W | FactoryReset | no |
| 1033 | …-0002-… | 33 | RW | Security | no |
| 1034 | …-0002-… | 74 | RW | SlaveInfo | no |
| 1037 | …-0003-… | 3 | RW | FunctionRule | no |
| 2001 | …-0003-… | 3 | R | SwVersion | yes |
| 2002 | …-0003-… | 6 | RW | Gdid | yes |
| 2004 | …-0003-… | 20 | RW | Brand | yes |
| 2005 | …-0003-… | 6 | RW | HeaterType | yes |
| 2006 | …-0003-… | 5 | RW | Btpk | yes |
| 2007 | …-0003-… | 16 | RW | EncKey | yes |
| 2008 | …-0003-… | 16 | RW | AuthKey | yes |
| 200a | …-0003-… | 6 | RW | EpIdentifier | yes |
| 2012 | …-0003-… | 5 | RW | FirmwareVersion | no |
| 300e | …-0001-… | 1 | RW | Esp32OtaEnable | no |
| 4012 | …-0000-… | 1 | R | HeatSetting | no |
| 7005 | …-0004-… | 1 | R | DsmMode | no |
| 7006 | …-0004-… | 1 | R | SeasonalBand | no |
| 7007 | …-0004-… | 2 | R | OffpeakCounter | no |
| 7008 | …-0004-… | 3 | R | Runtime | no |
| 700b | …-0005-… | 3 | RW | ChargeMode | no |
| 700e | …-0005-… | 4 | RW | ExternalController | no |
| 701f | …-0001-… | 9 | R | RelayStatus | no |
| 7020 | …-0000-… | 3 | RW | ButtonPressOperation | no |
| 7021 | …-0003-… | 4 | RW | HeatingModeSetpoint | no |
| 7022 | …-0003-… | 4 | RW | PresetButtonSetpoint | no |
| 7024 | …-0003-… | 12 | R | PcbStatus | no |
| 7026 | …-0000-… | 8 | RW | ActivateProduct | no |
| 7029 | …-0003-… | 1 | RW | ErrorTone | no |

Present on the Q-Rad but not named by ConfigR: 0001 (backlight colour, from
observation), 000b, 000c, 1003, 100a, 100b, 100f, 1012-1015, 1022, 1029, 1050,
2003, 2009, 200b, 200c, 200d, 200f.

### Selector characteristics: write, then read

Several parameters multiplex more than one value through one characteristic.
ConfigR's read routine writes a selector, then reads:

| Char | Name | Write | Read back |
|---|---|---|---|
| 0008 | TemperatureSensor | `[n, 0, 0]`, n = 1 room, 2 LCD, 3 core | `[n, whole, tenths]`, °C = whole + tenths/10 |
| 0002 | Trac | `[n, 0, 0]`, n = element 1 or 2 | `[n, active]` |
| 2001 | SwVersion | `[n, 0, 0]`, n = 0 controller, 1 UI, 2 RF | `[n, major, minor]` |
| 7008 | Runtime (not on Q-Rad) | `[n, 0, 0]`, n = 0..4 | runtime counters |
| 0003 | Relay (not on Q-Rad) | `[n, 0]` | relay state |

This is why the plain reads returned zeros all morning: nothing had been
selected. **Confirmed on the Q-Rad 2026-09-11 15:0x**: write `[1,0,0]` to 0008
then read gave `01 18 05` = 24.5 °C against 24.4 on the debug screen; 0002
gave `01 00` with the element idle. The ESPHome node now does both every 30 s.

### Decoders worth having

- **000a PowerLoading**: `[e1 lo, e1 hi, e2 lo, e2 hi, 0, 0, 0, 0]`, rated watts
  per element. Q-Rad 100E reads 1000 and 2200. Live power = rated x element active.
- **1011 ErrorStatus**: one byte, fault code id, 0 = no error.
- **0007 LastKeyPressValue**: last button pressed, not a screen index.
- **1016 Setback**: 2 bytes. **1017 Runback**, **1027 RunbackTime** (boost
  countdown), **1028 RunbackSetpoint** (boost default): ConfigR's names for the
  boost family.
- **1007 OpenWindowDetection** (9 bytes), **1008 PreEmptiveHeating** (adaptive
  start), **1005 TemperatureUnit**, **100c RfComms**, **0005 Sound**,
  **1019 SpConfig**, **100e OtaEnable**, **1020 TestMode**, **1010 EolTest**.
- **2002 Gdid**, **2004 Brand**, **2005 HeaterType**, **200a EpIdentifier**,
  **2006 Btpk**, **2007 EncKey**, **2008 AuthKey** (the last three are the
  property-less ones; leave alone).
- **1024 HeatDemand** `[band, temperature]` exists in ConfigR but not on this
  radiator's firmware.
- **0006 SetRtc** is write-only in ConfigR (7 bytes); **0106 SetRtcWithSeconds**
  (8 bytes) is the newer form. ConfigR writes the RTC as its connection test.
- **700f Disconnect**: ConfigR writes `[1]` here to make the radiator drop the
  link cleanly. Not present on the Q-Rad D.

ConfigR pairs with a plain BLE bond and only performs its extra
`SecurityParameter` (1033) handshake on products that expose it. The Q-Rad D
does not, so there is no app-level authorisation.

## Watch session 1, 2026-09-11 09:38

User changed setpoint, modes, boost on the QRAD100E while `ble_watch.py`
polled. Raw output:

```
09:38:55 h=  29 00001003  0f00  ->  1200
09:38:55 h=  31 00001023  0f00  ->  1200
09:38:56 h=  64 00000001  02b9ff96  ->  02ff7878
09:38:56 h=  68 00000007  03  ->  04
09:38:58 h=  25 00001001  030000000000  ->  020000000000
09:38:59 h=  29 00001003  1200  ->  1700
09:38:59 h=  31 00001023  1200  ->  1700
09:39:00 h=  64 00000001  02ff7878  ->  0200ff00
09:39:00 h=  68 00000007  04  ->  01
09:39:02 h=  23 00000006  141a090b090f01  ->  141a090b091001
09:39:02 h=  25 00001001  020000000000  ->  030000000000
09:39:02 h=  29 00001003  1700  ->  1200
09:39:02 h=  31 00001023  1700  ->  1200
09:39:03 h=  64 00000001  0200ff00  ->  02b9ff96
09:39:03 h=  68 00000007  01  ->  02
09:39:07 h=  68 00000007  02  ->  01
09:39:10 h=  57 00001027  0000  ->  1e00
09:39:10 h=  68 00000007  01  ->  03
09:39:12 h=  25 00001001  030000000000  ->  020000010000
09:39:12 h=  29 00001003  1200  ->  1700
09:39:12 h=  31 00001023  1200  ->  1700
09:39:14 h=  68 00000007  03  ->  06
09:39:16 h=  25 00001001  020000010000  ->  020000000000
09:39:16 h=  29 00001003  1700  ->  1200
09:39:16 h=  31 00001023  1700  ->  1200
09:39:17 h=  57 00001027  1e00  ->  0000
09:39:17 h=  68 00000007  06  ->  03
09:39:19 h=  25 00001001  020000000000  ->  030000000000
09:39:19 h=  29 00001003  1200  ->  0d00
09:39:19 h=  31 00001023  1200  ->  0f00
09:39:20 h=  64 00000001  02b9ff96  ->  0287ceeb
09:39:20 h=  68 00000007  03  ->  04
09:39:23 h=  29 00001003  0d00  ->  0f00
```

Correction after session 2: the radiator was in Eco (mode 3) here, not Manual.
Boost switches to mode 2 (Manual) with byte 3 set and carries its own setpoint
(23) in 1023. The brief mode 2 at 09:38:58 was likely the boost screen opened
and backed out of. Nothing that looks like a live room temperature changed
during the session; 000a was later ruled out (see Next).

## Watch session 2, 2026-09-11 10:05, mode enumeration

Marks were typed after each action. Raw output:

```
10:05:51 MARK: start manual        (radiator was actually in Eco, mode 3)
10:06:07 1003/1023 0f00 -> 1200    setpoint nudged to 18
10:06:13 MARK: eco                 no mode change: already 3
10:06:25 1001 03.. -> 04..         Frost Protect
10:06:25 1003/1023 -> 0700         7 C
10:06:26 0001 -> 0200008c          deep blue backlight
10:06:35 MARK: frost
10:06:56 1001 04.. -> 01 03 ..     Timer, sub-mode 3 = User Timer
10:07:11 MARK: user timer
10:07:27 1001 -> 01 02 ..          sub-mode 2 = Home All Day
10:07:28 1003/1023 -> 1500         21 C period
10:07:43 MARK: home all day
10:08:02 1001 -> 01 01 ..          sub-mode 1 = Out All Day
10:08:02 1003/1023 -> 0700         7 C (heating off period)
10:08:11 MARK: out all day
10:09:11 1001 -> 01 05 ..          sub-mode 5 = Away
10:09:12 102a 00000101000007 -> 011a090c2e0907   away active until 2026-09-12 09:46, 7 C
10:09:26 MARK: away, had to set it until tomorrow
10:09:39 1001 -> 01 01 ..          back to Out All Day
10:09:40 102a -> 001a090c2e0907    away cleared
10:09:43 1003/1023 -> 1500, 100d 00 -> 01    Advance engaged, heating on period
10:09:55 MARK: advance on
10:10:00 1003/1023 -> 0700, 100d 01 -> 00    Advance released
10:10:10 MARK: advance off
10:10:31 1001 -> 02 00 ..          Manual
10:10:31 1003/1023 -> 1500         21 C
10:10:37 MARK: manual
```

Advance is not offered while in Away. Clock minute byte ticked 2a..2f over
the session, radiator clock still 22 min slow.

## Write session 3, 2026-09-11 ~10:25, Manual/Eco relationship

```
start                        mode=03 (Eco)    setpoint=15
write mode 2 (Manual)        mode=02 (Manual) setpoint=21
write setpoint 15            mode=03 (Eco)    setpoint=15
write setpoint 21            mode=02 (Manual) setpoint=21
write setpoint 18            mode=03 (Eco)    setpoint=18
write setpoint 19            mode=03 (Eco)    setpoint=19
write mode 3 (Eco)           mode=03 (Eco)    setpoint=18
write setpoint 22 in Eco     mode=02 (Manual) setpoint=22
restore mode 3               mode=03 (Eco)    setpoint=18
restore setpoint 15          mode=03 (Eco)    setpoint=15
```
