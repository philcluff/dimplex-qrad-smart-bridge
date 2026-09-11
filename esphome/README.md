# ESPHome nodes

> [!NOTE]
> This file was written by Claude during the build, from the bring-up of the first node on the bench and the logs it produced. The steps were followed once, on one radiator; expect to adjust them for the next.

One Waveshare ESP32-S3-Zero per radiator. `qrad-common.yaml` is the shared
package; each radiator gets a small file with three substitutions (`name`,
`friendly_name`, `radiator_mac`) and optionally `led_pin`.

## Entities per radiator

Entity ids are derived by Home Assistant from the device's friendly name at
adoption, e.g. `number.office_radiator_target_temperature`.

- **Target Temperature** (number) - the control. 7 to 30 °C, whole degrees.
  Non-optimistic: shows what the radiator reports. If the radiator is in Timer
  or Frost Protect it is forced to Manual first. Unavailable when disconnected.
- **Setpoint (radiator)** (sensor) - raw read of characteristic 0x1023, every 30 s.
- **Room Temperature** (sensor) - the radiator's own room sensor, 0.1 °C, every 30 s via a selector write to 0x0008.
- **Heating** (binary sensor) - element 1 on or off, every 30 s via a selector write to 0x0002.
- **Power** (sensor) - rated watts while heating, else 0. **Rated Power** (diagnostic) - from 0x000a, hourly.
- **Mode** (text sensor) - Timer / Manual / Eco / Frost Protect. Blank when disconnected.
- **Radiator Connected** (binary sensor, diagnostic).
- **Radiator RSSI** (sensor, diagnostic) - live link RSSI every 10 s. Use it to
  site the node: better than -75 dBm solid, -75 to -85 works with occasional
  retries, worse than -85 expect drops. A node 3 m away in the same room
  measured -71 to -79. The radiator's antenna sits behind the plastic control
  panel, so face that end rather than the steel back.
- **Model** (text sensor, diagnostic) - e.g. `QRAD100E;D;`, read hourly.
- **Pairing Passkey** (text, config) - enter the six digits shown on the
  radiator, once. Clears itself after submitting. Inert when already bonded.
- **Force Manual**, **Clear BLE Bonds**, **Restart** (buttons).
- Onboard LED at 50%: green connected, amber not connected (searching,
  radiator off, or waiting for a passkey). Does not reflect Wi-Fi. Channel
  order on the S3-Zero's WS2812 is RGB, pin GPIO21; Super Mini clones use GPIO48
  via the `led_pin` substitution.

## Bringing up a new radiator

1. On the radiator: Menu > Settings > Comms > Bluetooth, enable. Disconnect
   any phone app; the radiator accepts one central at a time.
2. Copy `qrad-office.yaml` to `qrad-<room>.yaml`, set `name` and
   `friendly_name`, leave `radiator_mac` as zeros.
3. First flash over USB, from the repo root:
   `mise run esphome-run esphome/qrad-<room>.yaml --device /dev/cu.usbmodemXXXX`.
   The S3-Zero's native USB auto-resets into the bootloader; if esptool can't
   connect, hold BOOT while plugging in and try again.
4. Watch the log for `Unconfigured Dimplex advert: AL9502<Dimplex> mac=XX:XX:XX:XX:XX:XX`.
   Put that MAC in the yaml and run again (OTA from now on, `--device <name>.local`).
5. The node connects and the radiator displays a passkey. Enter those digits
   in the Pairing Passkey box within about 30 s, either in Home Assistant or on
   the node's own page at `http://<name>.local/`. If the code changes before
   you submit, use the new one; the node retries every ~30 s.
6. LED goes green, Model reads the radiator's model string, setpoint populates.

The bond is stored in the node's NVS and on the radiator, so re-pairing is only
needed after Clear BLE Bonds or a factory reset on either side. Both sides
surviving a power cut has been tested.

## Driving it without Home Assistant

The node runs ESPHome's web server. Routes use the entity display name:

```
curl -X POST -d '' 'http://<name>.local/number/Target%20Temperature/set?value=21'
curl -X POST -d '' 'http://<name>.local/button/Force%20Manual/press'
curl 'http://<name>.local/text_sensor/Mode'
curl -H 'Accept: text/event-stream' http://<name>.local/events     # all states
```

POST needs a body, even an empty one, or the server returns 411.

## Lessons from bring-up

- On ESP-IDF the node must call `esp_ble_set_encryption()` after connecting or
  every encrypted read fails with GATT status 15 and no passkey prompt appears.
  The Sunhouse config got this implicitly on the Arduino stack.
- Delayed action chains off the BLE `on_connect` trigger are unreliable;
  refreshes are driven from the 2 s interval and from the mode sensor's own
  lambda instead.
- `0x2005` (model string) lives under service `...-0003-...`, not the main one.
- Room temperature, element state and firmware versions are selector
  characteristics: write `[n,0,0]` then read, or you get zeros. The 30 s
  interval in the package does the writes; the sensors have `update_interval:
  never` and are updated from that interval so the read always follows its write.
- The WS2812 on the S3-Zero is RGB order, not GRB as some guides say. Green
  showing as red is the tell.
- A non-optimistic template number with no value shows "NaN" on the ESPHome
  web page. Home Assistant shows it as unavailable, which is the intent.

## Not done

- No keep-alive is written. A node polling every 10 s has held its connection
  for hours; a truly idle connection is untested. `auto_connect` covers drops.
- Clock sync is on the backlog: 0x0006 is writable and the radiators run slow.
