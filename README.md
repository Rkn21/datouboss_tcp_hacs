# Datouboss TCP for Home Assistant

Custom Home Assistant integration for Datouboss / Voltronic-compatible inverters connected through a transparent RS232-to-TCP gateway such as the **EBYTE NE2-D14PE**.

This integration polls the inverter over TCP, parses the common Voltronic/Axpert responses, exposes sensors, and provides service actions to send raw commands or common write commands.

## Features

- UI setup via **config flow**
- HACS-ready repository structure
- Polling over **TCP** to an RS232 bridge
- Sensors for:
  - inverter mode
  - serial number
  - grid voltage/frequency
  - output voltage/frequency
  - apparent/active power
  - load percent
  - DC bus voltage
  - battery voltage/current/capacity
  - heatsink temperature
  - PV voltage/current/power
  - warning bitfield
- Select entities for:
  - output source priority
  - charger source priority
  - AC input range
  - max AC charge current
  - max total charge current
- Service actions for sending commands:
  - `datouboss_tcp.send_command`
  - `datouboss_tcp.refresh`
  - `datouboss_tcp.set_output_source_priority`
  - `datouboss_tcp.set_charger_source_priority`
  - `datouboss_tcp.set_ac_input_range`
  - `datouboss_tcp.set_max_ac_charge_current`
  - `datouboss_tcp.set_max_total_charge_current`

## Tested protocol basis

This integration is built around the Voltronic-compatible command set used by many Datouboss / Axpert-like inverters, including commands such as `QID`, `QMOD`, `QPIGS`, `QPIRI`, `QPIWS`, `QMCHGCR`, and `QMUCHGCR`.

## Installation with HACS

1. Put this repository on GitHub.
2. In Home Assistant, open **HACS → Integrations → ⋮ → Custom repositories**.
3. Add your GitHub repository URL as type **Integration**.
4. Install **Datouboss TCP**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration**.
7. Search for **Datouboss TCP**.

## Configuration

The config flow asks for:

- **Host**: IP of your TCP/RS232 gateway
- **Port**: TCP port of the gateway (often `8886`)
- **Name**: friendly display name
- **Scan interval**: polling interval in seconds
- **Timeout**: per-request timeout in seconds

## Wiring note for EBYTE NE2-D14PE

If your Datouboss RJ45 COM port uses:

- pin 3 = TX
- pin 4/5 = GND
- pin 6 = RX

and the NE2 DB9 uses:

- pin 2 = TX
- pin 3 = RX
- pin 5 = GND

then the working wiring for the NE2 is:

- inverter RJ45 pin **3** → NE2 DB9 pin **3**
- inverter RJ45 pin **4 and/or 5** → NE2 DB9 pin **5**
- inverter RJ45 pin **6** → NE2 DB9 pin **2**

## Service examples

### Send a raw command

```yaml
action: datouboss_tcp.send_command
data:
  config_entry_id: YOUR_CONFIG_ENTRY_ID
  command: QPIGS
```

### Set output source priority to SBU

```yaml
action: datouboss_tcp.set_output_source_priority
data:
  config_entry_id: YOUR_CONFIG_ENTRY_ID
  mode: sbu_priority
```

### Set charger source priority to solar only

```yaml
action: datouboss_tcp.set_charger_source_priority
data:
  config_entry_id: YOUR_CONFIG_ENTRY_ID
  mode: solar_only
```

### Set max AC charge current

```yaml
action: datouboss_tcp.set_max_ac_charge_current
data:
  config_entry_id: YOUR_CONFIG_ENTRY_ID
  amps: 10
```

## Known limitations

- This integration targets the common Voltronic-compatible command set. Clones or firmware variants may expose different commands or fields.
- The write services do not attempt to expose every possible inverter setting; `send_command` is included for advanced use.
- The response parser is strict enough for typical `QPIGS` / `QPIRI` frames, but some firmware variants may reorder fields.

## Publishing note

Before publishing this on GitHub, update these placeholder URLs in `custom_components/datouboss_tcp/manifest.json`:

- `documentation`
- `issue_tracker`

