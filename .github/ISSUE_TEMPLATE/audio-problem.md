---
name: Audio problem or hardware validation
about: Report a failure or a separately verified hardware result
---

## Hardware and software

- Exact model (`cat /sys/class/dmi/id/product_name`):
- Distribution and version:
- Kernel (`uname -r`):
- PipeWire and alsa-ucm-conf versions:
- Audio controller / subsystem ID:
- Previous audio workarounds installed:

## Symptom

Describe what happens, when it started, and whether the problem occurs on boot, after sleep, or continuously.

## Separate test results

- Audible speaker playback:
- Both channels:
- Reboot:
- Suspend/resume:
- Headphones (if tested):

## Diagnostics

Attach selected output from `python3 scripts/px13_audio.py diagnose` and the relevant recovery-service log. Remove personal information. Include exact requested firmware filenames and both amplifier attachment states.

Do not upload proprietary firmware, the ASUS installer, or an entire unrelated system journal.

## Steps attempted

List changes and results, including the firmware package version and whether checksums matched.
