# Research notes

> [!NOTE]
> This file was written by Claude during the research, from Dimplex and GDHV documentation, retailer listings, Home Assistant community threads and the GitHub projects it links. It records what was found and why the BLE route was chosen; the sources are listed at the bottom so the claims can be checked.

Date: 2026-09-11

## The Dimplex Control ecosystem

Dimplex Control is a cloud system. Every command goes app to Azure cloud to
Dimplex Hub to appliance. The hub needs an always-on internet connection and
exposes no local API. Hub outbound ports are 443 and 5671 (AMQPS, Azure IoT Hub).
The hub's Bluetooth is only used for first-time setup. The hub spec sheet lists
an RS485 port whose purpose is undocumented.

### Hub to appliance radio

- 868 MHz, 6LoWPAN mesh (802.15.4g), AES-128 link encryption.
- Hub holds certificates and keys in a separate anti-tamper crypto chip.
- Q-Rad RF models have this built in. Q-Rad E models need the plug-in RFM
  (part 071569, about £40) which replaces the coin-cell battery tray.

Conclusion: emulating the hub means implementing 15.4g, 6LoWPAN, the join and
key exchange, and the application layer, with no way to capture a join without
a real hub. Not worth pursuing.

### The RFM slot

The blank tray in a Q-Rad E holds the CR2032 for the RTC. The RFM replaces it
and carries its own cell. Fault codes 22/40 "Internal serial comms error",
60 "Wireless communication module error" and 61 "Hub connection error" show a
bidirectional serial link between the controller and the module. The manuals
leak the phrase "Each error code must be defined as a parameter that Central
Control can read", so the application model is a parameter get/set.

The Comms menu lists "RF Module" and "Bluetooth" even with no RFM fitted.
Pinout of the slot is not yet probed. This route is parked because BLE works.

### Built-in Bluetooth

The Q-Rad E spec sheet lists "Bluetooth for software updates". In practice the
BLE interface exposes the whole control surface (see `ble-protocol.md`).
Pairing is BLE passkey display: the radiator shows a six-digit code, the
central enters it, both bond. No cloud involvement. The Bluetooth radio is a
Cypress PSoC 4 BLE module (its OTA bootloader service is present), consistent
with the Quantum Hybrid UI board teardown.

Dimplex's ConfigR installer app (`com.Dimplex.DimplexToolkit`) uses this
interface for configuration and firmware updates.

## Prior art

- JYewman/Sunhouse-Dimplex-Storage-Heater-ESPHome-Home-Assistant. Glen Dimplex
  Sunhouse SSHE storage heater controlled from an ESP32 over BLE using ESPHome.
  Protocol reversed from the Dimplex Remo Android app (`com.dimplex.remo`).
  Same service UUID and characteristic numbering as the Q-Rad. This is the
  template for our implementation.
  https://github.com/JYewman/Sunhouse-Dimplex-Storage-Heater-ESPHome-Home-Assistant
- bobthecooldad/Dimplex-Quantum-Storage-Heater-Dump. PCB photos and SPI flash
  dump of a Quantum Hybrid UI board (GD_Quantum_Hybrid_UI_XLE_v4_5). Shows the
  GDHV pattern: main MCU, Cypress CY8C4248LQI-BL BLE module, Macronix flash,
  coin cell, debug headers.
  https://github.com/bobthecooldad/Dimplex-Quantum-Storage-Heater-Dump
- KRoperUK/dimplex-controller-py and dimplex-controller-hass. Cloud API client
  for the hub (`api.gdhv.io`, Azure B2C). Only relevant if a hub is present.
  Useful as a map of the command set.
- Home Assistant threads (2019 to 2025) on Q-Rad and Dimplex Hub integration
  contain no technical findings. Dimplex told a user they have no plans for
  Matter or third-party integration.
- Terma MOA Blue projects are a different protocol (D97352Bx UUIDs). The
  Sunhouse repo's `terma_ble_helper.h` is just a filename, not Terma code.

## Sources

- Dimplex Hub Series A spec sheet:
  https://www.dimplex.eu/sites/g/files/emiian586/files/media_import/medias/docus/13/DimplexHub%20Series%20A%20Spec%20Sheet%20-%20Issue%202.pdf
- Dimplex Control product catalogue 2021 (RFM spec: 868MHz, 6LoWPAN, AES-128):
  https://www.dimplex.co.uk/sites/g/files/emiian551/files/2023-08/iot_product_catalogue_2021.pdf
- RFM installation instructions:
  https://www.electricpoint.com/media/productattachments/files/d/i/Dimplex-RFM-Instructions.pdf
- Dimplex Control compatibility list:
  https://www.dimplex.co.uk/products/dimplex-control/compatibility
- GDHV help, cloud architecture:
  https://help.gdhv.co.uk/support/solutions/articles/79000136832-what-does-the-dimplex-control-cloud-run-on-and-how-is-my-data-kept-safe-
- GDHV help, hub Bluetooth:
  https://help.gdhv.co.uk/support/solutions/articles/79000136841-what-is-bluetooth-used-for-on-the-dimplex-hub-
- GDHV help, RFM not connecting:
  https://help.gdhv.co.uk/support/solutions/articles/79000139612-my-product-s-radio-frequency-model-rfm-isnt-connecting-to-the-hub-why-
- Q-Rad E manual, Series D (08/82339/0 Issue 3):
  https://manuals.plus/dimplex/qrad050e-q-rad-electric-radiator-manual
- Q-Rad RF manual, Series G (08/82904/0 Issue 3):
  https://www.dimplex.co.uk/sites/g/files/emiian551/files/media_import/medias/docus/13/QRAD%20RF%20Instruction%20Manual%20Series%20G%20-%20Issue%203.pdf
- ConfigR app page: https://www.dimplex.co.uk/products/smart-controls/configr
