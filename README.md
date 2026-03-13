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
  - battery voltage/current/capacity, including discharge current
  - heatsink temperature
  - PV voltage/current/power
  - inverter rating and battery profile values reported by `QPIRI`
  - diagnostic snapshots exposing parsed `QPIGS` / `QPIRI` data and raw payloads
  - warning bitfield
- Binary sensors for decoded inverter state flags:
  - output active
  - charge active
  - SCC charging
  - AC charging
  - floating mode
  - inverter on
- Select entities for:
  - output source priority
  - charger source priority
  - AC input range
  - max AC charge current
  - max total charge current
- Number controls for verified writable voltage settings:
  - battery under voltage (`PSDV`, 42.0 V to 48.0 V, user battery type only)
- Additional controls for verified writable settings:
  - `QFLAG` option switches for buzzer, bypass, LCD auto return, auto restart, backlight, source-interrupt beep, and fault-code record
  - battery type (`PBT00`/`01`/`02`)
  - output voltage (`V220`/`V230`/`V240`)
  - output frequency (`F50`/`F60`)
  - battery recharge, redischarge, bulk, and float voltages (`PBCV`, `PBDV`, `PCVV`, `PBFT`)
  - battery equalization state and parameters via `QBEQI` / `PBEQ*`

Only parameters with a verified write command are exposed as Home Assistant controls. Other `QPIRI` values are still exposed as sensors until their corresponding write commands are confirmed.
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

### QPIRI reference

`QPIRI` is parsed as nominal and configuration data in this order:

1. AC input rating voltage
2. AC input rating current
3. AC output rating voltage
4. AC output rating frequency
5. AC output rating current
6. AC output rating apparent power
7. AC output rating active power
8. Battery rating voltage
9. Battery recharge voltage
10. Battery under voltage
11. Battery bulk voltage
12. Battery float voltage
13. Battery type
14. Max AC charge current
15. Max total charge current
16. AC input voltage range
17. Output source priority
18. Charger source priority
19. Parallel max number
20. Machine type
21. Topology
22. Output mode
23. Battery redischarge voltage
24. PV OK condition

Known interpretations used by the integration include:

- Battery type: `0=agm`, `1=flooded`, `2=user`, `3=lithium`
- AC input range: `00=appliance`, `01=ups`
- Output source priority: `00=utility_first`, `01=solar_first`, `02=sbu_priority`
- Charger source priority: `00=utility_first`, `01=solar_first`, `02=solar_and_utility`, `03=solar_only`
- Machine type: `00=grid_tie`, `01=off_grid`, `10=hybrid`
- Topology: `0=transformerless`, `1=transformer`
- Output mode: `0=single_machine`, `1=parallel_output`, `2=phase_1_of_3_phase`, `3=phase_2_of_3_phase`, `4=phase_3_of_3_phase`
- PV OK condition: `0=pv_ok_if_one_inverter_has_pv`, `1=pv_ok_if_all_inverters_have_pv`

Example for the frame `240.0 25.8 240.0 50.0 25.8 6200 6200 48.0 50.0 44.8 58.4 54.0 2 02 050 1 2 1 9 01 0 0 54.0 1`:

- Battery type: `2 -> user`
- AC input range: `1 -> ups`
- Output source priority: `2 -> sbu_priority`
- Charger source priority: `1 -> solar_first`
- Machine type: `01 -> off_grid`
- Topology: `0 -> transformerless`
- Output mode: `0 -> single_machine`
- PV OK condition: `1 -> pv_ok_if_all_inverters_have_pv`

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

