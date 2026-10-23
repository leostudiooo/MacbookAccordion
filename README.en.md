# Lid Accordion

[繁體中文](README.md)

A side project that turns your MacBook into a virtual accordion by using the lid opening angle as the bellows.

Built in spare time at work, developed step by step with the help of ChatGPT.

---

## Overview

- Reads the MacBook lid angle sensor to simulate accordion bellows push/pull motion
- Play notes via keyboard keys; audio is synthesized in real time using `PolyAccordionSynth`
- Provides a GUI parameter panel for live adjustment of bellows sensitivity, timbre, and more
- Provides `Classic Saw` and `Tutorial Reed` timbres with a top-level selector for instant comparison
- Automatically falls back to simulation mode (↑↓ keys control angle) when the physical sensor is unavailable

The application still starts from `lid_accordion.py`. Audio, input, keyboard mappings,
parameters, and GUI controls now live in the `accordion/` package; the main loop and user
interaction remain unchanged.

---

## Technical Reference

The method for reading the MacBook Lid Angle Sensor is based on:

> [https://github.com/samhenrigold/LidAngleSensor](https://github.com/samhenrigold/LidAngleSensor)

---

## Requirements

| Item | Version / Notes |
|------|----------------|
| OS | macOS |
| Python | 3.x |
| Main packages | `pygame`, `numpy`, `sounddevice`, `pybooklid` |

---

## Build & Run

### 1. Package as a .app bundle

```bash
cd lid_accordion_mac_app_sounddevice
chmod +x build_mac_app.sh
./build_mac_app.sh
```

After packaging, the executable is located at:

```
dist/LidAccordion.app/Contents/MacOS/LidAccordion
```

### 2. Run directly with Python (development)

```bash
pip install pygame numpy sounddevice pybooklid
python lid_accordion.py
```

---

## Key Bindings

The keyboard is mapped to two continuous chromatic ranges, starting at C on `Q` and `Z`.

### Group 1 (Mid range, MIDI 60–80)

```text
Q 2 W 3 E R 5 T 6 Y 7 U I 9 O 0 P [ = Backspace \
C4 C#4 D4 D#4 E4 F4 F#4 G4 G#4 A4 A#4 B4 C5 C#5 D5 D#5 E5 F5 F#5 G5 G#5
```

### Group 2 (High range, MIDI 72–87)

```text
Z S X D C V G B H N J M , L . ; /
C5 C#5 D5 D#5 E5 F5 F#5 G5 G#5 A5 A#5 B5 C6 C#6 D6 D#6 E6
```

### Octave Transpose

| Action | Effect |
|--------|--------|
| Release `Shift` | Shift up one octave (+12 semitones) |
| Release `Ctrl` | Shift down one octave (−12 semitones) |
| `Tab` | Reset to default octave (0) |

### Simulation Mode (when sensor is unavailable)

| Key | Effect |
|-----|--------|
| `↑` | Increase simulated lid angle (bellows open faster) |
| `↓` | Decrease simulated lid angle (bellows contract) |
| Mouse wheel | Scroll within the parameter panel |

---

## GUI Parameters

| Parameter | Description |
|-----------|-------------|
| Bellows sensitivity | Maximum bellows speed (affects angular velocity → volume mapping) |
| Ignore tiny movement | Dead zone threshold to ignore small tremors |
| How fast air builds | Air pressure accumulation rate |
| How fast air leaks | Air pressure leak rate |
| Volume rise smoothness | Smoothing coefficient for volume increase |
| Volume fall smoothness | Smoothing coefficient for volume decrease |
| Overall volume | Master volume |
| Note attack time | Note fade-in time (seconds) |
| Note release time | Note fade-out time (seconds) |
| Reed thickness (detune) | Dual sawtooth wave detune amount, simulating accordion reed thickness |
| Air / reed noise | Amount of airflow and reed noise |
| Reed filter cutoff | Low-pass cutoff for `Tutorial Reed` |
| Filter resonance | Low-pass resonance for `Tutorial Reed` |
| Chorus mix | Stereo chorus mix for `Tutorial Reed` |
| Chorus rate (Hz) | Chorus modulation rate for `Tutorial Reed` |

### Timbres

- `Classic Saw`: the original dual-saw, lightly detuned timbre.
- `Tutorial Reed`: the tutorial-inspired root saw, octave-up square wave, low-pass filter, and stereo chorus.

---

## Roadmap

- [ ] Improve key layout for a more intuitive range mapping that better matches a real accordion keyboard
- [ ] Consider adding different timbres (tremolo, musette tuning, etc.)

---

## Version

`0.0.1` (Bundle ID: `games.macaca.lidaccordion`)
