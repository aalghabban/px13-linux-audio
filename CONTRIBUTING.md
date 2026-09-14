# Contributing

Include exact hardware and software versions with every report. Keep confirmed observations separate from hypotheses. Report speaker playback, reboot, and sleep recovery as independent results.

For another model, first collect read-only diagnostics and identify the exact codec combination and official firmware. Do not broaden the hardware or firmware allowlist based only on a matching product family.

Run the automated checks from the repository root:

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/extract-firmware.sh
python3 scripts/px13_audio.py --help
```

Tests use temporary paths and mocks. They must never write real firmware, change the host's audio service state, or remove PCI devices. Hardware tests must be explicit and documented separately.

Do not commit calibration blobs, driver installers, extracted binaries, or personal diagnostic logs. The issue template and upstream draft are provided for reports; no report is submitted automatically.
