# SwitchBot Cover Integration for Home Assistant

A custom Home Assistant integration that creates unified cover entities from pairs of SwitchBot Bot switches (up/down) with optional contact sensor feedback.

## Why?

Many roller shutters use wall-mounted buttons — one for up, one for down. SwitchBot Bots can press these buttons via BLE, but each Bot appears as an independent `switch` entity in Home Assistant. This integration wraps a pair of SwitchBot switches into a proper `cover` entity with:

- **Open / Close / Stop** controls
- **Movement lockout** — prevents conflicting up/down commands while the shutter is moving
- **Contact sensor feedback** — tracks open/closed state via an optional door/window sensor
- **Position support** — binary position (0% or 100%) based on the contact sensor
- **UI configuration** — no YAML editing required

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Add `https://github.com/ovflowd/switchbot-cover-integration` as an **Integration**
4. Search for "SwitchBot Cover" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/switchbot_cover/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **SwitchBot Cover**
3. Fill in:
   - **Cover name** — friendly name (e.g., "Bedroom Rollers")
   - **Up switch** — the SwitchBot switch entity that opens the shutter
   - **Down switch** — the SwitchBot switch entity that closes the shutter
   - **Contact sensor** (optional) — a binary sensor that detects shutter position (`on` = open, `off` = closed)
   - **Movement timeout** — seconds to wait for movement to complete (default: 30s)
4. Click **Submit**

Repeat for each roller shutter. The contact sensor and timeout can be changed later via the integration's options.

## How it works

When you send an **open** or **close** command:

1. The integration checks the movement lock — if the shutter is already moving, the command is ignored
2. The lock is acquired
3. The corresponding SwitchBot switch is toggled (simulating a button press)
4. The integration waits for the contact sensor to report the expected state, or for the timeout to elapse
5. The lock is released

**Stop** re-toggles the active direction switch, which on most roller shutter controllers acts as a stop command.

**Position** is binary: 100% (open) or 0% (closed), derived from the contact sensor. `set_position` with a value > 50% opens, ≤ 50% closes.

## Requirements

- Two SwitchBot Bot switches per roller shutter (configured via the SwitchBot BLE integration)
- Optionally, a contact/door sensor attached to the shutter for state feedback

## License

MIT
