# ASUS ProArt PX13 HN7306EAC: Linux speaker repair

A documented workaround for silent internal speakers and **Dummy Output** on the ASUS ProArt PX13 HN7306EAC running Ubuntu 26.04.

On the tested machine, the repair restored audible stereo playback by combining:

1. The matching TAS2783 amplifier firmware from ASUS's driver package.
2. An ALSA UCM speaker definition and a correction for an unavailable headphone control.
3. Firmware aliases matching the kernel's actual `FFFF-1-8.bin` / `FFFF-1-B.bin` requests.
4. Audio PCI removal and rescan when driver unbind/bind left both amplifiers `UNATTACHED`.

**Scope:** one confirmed HN7306EAC. This is not a universal PX13 fix. Other PX13 generations, firmware packages, kernels, and codec combinations need separate validation. The installer deliberately rejects other model names and hardware IDs.

## What has been verified?

| Check | Result |
| --- | --- |
| Exact ASUS firmware extracted and checksums verified | Passed |
| Both TAS2783 devices attached after audio PCI removal/rescan | Passed |
| Default output changed from Dummy Output to Audio Coprocessor Speaker | Passed |
| Browser stream routed to speakers | Passed |
| ALSA playback running at 48 kHz, stereo, S16_LE | Passed |
| Audible sound confirmed by the laptop owner | Passed |
| Fresh driver errors during the final 30-second observation | None |
| Reboot persistence | **Not yet tested** |
| Suspend/resume persistence | **Not yet tested** |
| New packaged installer on a clean installation | **Not yet tested** |

The manual repair was performed on **2026-09-14**. The scripts here package that procedure with hardware checks, checksum validation, backups, and rollback. Tests of the scripts do not replace hardware testing.

## Tested system

- Model: `ProArt PX13 HN7306EAC`
- OS: Ubuntu 26.04 LTS
- Kernel: `7.0.0-14-generic`
- PipeWire: `1.6.2`
- ALSA UCM package: `1.2.15.3-1ubuntu1`
- Firmware package: `20260319.git217ca6e4.1ubuntu`
- Audio controller: AMD PCI `0000:c4:00.5`, subsystem device `0x1714`
- Controller driver: `snd_pci_ps`
- ALSA machine driver: `snd_acp_sdw_legacy_mach`
- Codecs: RT721 headset codec and two TI TAS2783 SoundWire amplifiers

## Start here

Read [installation and rollback](docs/INSTALL.md) before making system changes.

```bash
# Run from a downloaded or cloned copy of this repository.
python3 scripts/px13_audio.py diagnose
```

Then [download and extract the ASUS firmware](docs/FIRMWARE.md). No firmware or Windows executable is distributed in this repository.

```bash
python3 scripts/px13_audio.py install --firmware-dir ./firmware --dry-run
sudo python3 scripts/px13_audio.py install --firmware-dir ./firmware
sudo python3 /usr/local/lib/px13-linux-audio/px13_audio.py recover
wpctl status
```

Close calls and recording sessions before recovery: it disconnects and re-enumerates the audio controller and restarts user audio services. The utility does not restart the computer.

## Documentation

- [Installation, affected files, backups, and rollback](docs/INSTALL.md)
- [Official ASUS download and firmware extraction](docs/FIRMWARE.md)
- [Observed failure chain and technical investigation](docs/INVESTIGATION.md)
- [Troubleshooting and verification](docs/TROUBLESHOOTING.md)
- [Draft upstream bug report](docs/UPSTREAM-ISSUE.md)
- [Contributing and reporting another hardware variant](CONTRIBUTING.md)
- [Sources and attribution](docs/SOURCES.md)
- [Packaging validation](docs/VALIDATION.md)
- [Publishing to GitHub](docs/PUBLISHING.md)

## Maintenance status

This is a local workaround, not an upstream driver patch. Package updates can overwrite the modified UCM files. If an upstream update fixes this hardware, prefer removing the workaround and testing the supported configuration. Do not assume that every later audio failure has the same cause.

Boot and post-sleep services are included and enabled by the installer. Their persistence behavior still needs a real reboot and sleep-cycle test on this machine. Systemd timeouts cannot guarantee interruption of a kernel operation stuck in uninterruptible sleep.

## License

Original scripts and documentation in this repository are available under the MIT license. ASUS/TI firmware is proprietary and excluded. The installer derives a local UCM override from the user's installed ALSA configuration; those upstream files retain their existing license. See [sources](docs/SOURCES.md).
