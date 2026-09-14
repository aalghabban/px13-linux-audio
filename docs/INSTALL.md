# Installation and rollback

## Before installation

This procedure is scoped to `ProArt PX13 HN7306EAC`, AMD audio PCI function `0000:c4:00.5`, vendor/device `0x1022:0x15e2`, subsystem `0x1714` (or the observed post-recovery `0xffff`), and `snd_pci_ps`. It requires Ubuntu-style ALSA UCM paths, systemd, Python 3, PipeWire, and WirePlumber.

1. Close audio calls and recording sessions.
2. Run `python3 scripts/px13_audio.py diagnose` as your normal user.
3. Read [the investigation](INVESTIGATION.md) and compare the errors with your machine.
4. Obtain the exact verified firmware using [FIRMWARE.md](FIRMWARE.md).
5. Run the dry-run command below and inspect the paths it prints.

If you already installed another repair, inspect its services and sleep hooks first. The installer refuses known old hooks at `/usr/lib/systemd/system-sleep/px13-audio-resume.sh` and `/usr/lib/systemd/system-sleep/50-px13-soundwire`. Back up and remove an obsolete hook only after establishing what it does. Running multiple recovery hooks can cause concurrent resets. Other custom service names cannot be detected automatically.

## Install

```bash
python3 scripts/px13_audio.py install --firmware-dir ./firmware --dry-run
sudo python3 scripts/px13_audio.py install --firmware-dir ./firmware
sudo python3 /usr/local/lib/px13-linux-audio/px13_audio.py recover
```

The dry run checks hardware, firmware hashes, and expected configuration inputs without changing system files. Installation saves a snapshot before replacing files. If file installation or service enablement fails, the installer attempts to restore that snapshot and reports errors.

Installation and live recovery are separate steps. An installer success message is not a playback test.

## Files written

| Path | Purpose |
| --- | --- |
| `/lib/firmware/1714-1-{8,B}.bin` | Exact ASUS calibration files |
| `/lib/firmware/FFFF-1-{8,B}.bin` | Same firmware under observed kernel-requested names |
| `/usr/share/alsa/ucm2/sof-soundwire/tas2783.conf` | Stereo SmartAmp playback on PCM 2 |
| `/usr/share/alsa/ucm2/sof-soundwire/rt721.conf` | Remove only the unavailable Headphone Switch cset commands |
| `/usr/share/alsa/ucm2/conf.d/amd-soundwire/ASUSTeKCOMPUTERINC.-ProArtPX13HN7306EAC-1.0-HN7306EAC.conf` | Model-specific speaker selection |
| `/usr/local/lib/px13-linux-audio/px13_audio.py` | Installed recovery and rollback utility |
| `/etc/systemd/system/px13-audio-rebind.service` | Boot recovery |
| `/etc/systemd/system/px13-audio-resume.service` | Recovery ordered after system sleep targets |
| `/var/lib/px13-linux-audio/` | Root-owned backup files and manifest |

The card override is derived from the installed generic UCM file, so the repository does not ship a frozen copy of the full upstream ALSA configuration. The change to `rt721.conf` is system-wide but removes only two unsupported control commands on this validated machine.

The recovery utility checks the hardware, serializes concurrent invocations, removes only the audio PCI function, rescans PCI, waits for the card and both amplifiers, and refreshes available user audio services. The rescan is system-wide discovery, not removal of all PCI devices.

## Verify now

```bash
wpctl status
systemctl is-enabled px13-audio-rebind.service px13-audio-resume.service
journalctl -k --since '2 minutes ago' --no-pager -g 'tas2783|snd_pci_ps'
```

The expected default sink is `Audio Coprocessor Speaker`. Start playback at a comfortable low volume and confirm both speakers produce sound. Older errors remain in the boot journal; compare timestamps with the latest recovery.

## Verify persistence separately

Save your work, then perform a normal reboot when convenient. Check `wpctl status` and audible playback again. Afterwards, test one suspend/resume cycle and repeat the checks.

```bash
journalctl -b -u px13-audio-rebind.service --no-pager
journalctl -b -u px13-audio-resume.service --no-pager
```

These checks have not yet been performed on the documented machine. Enabled services alone do not prove persistence.

## Roll back this installer

```bash
sudo python3 /usr/local/lib/px13-linux-audio/px13_audio.py uninstall
```

Rollback restores files and service enablement as they were immediately before this installer ran. Newly created files are removed. The snapshot is retained under `/var/lib/px13-linux-audio-restored-<timestamp>/`. Empty directories may remain. Restart the computer when convenient to clear already-loaded amplifier firmware.

If the installed utility is missing, use the repository copy:

```bash
sudo python3 scripts/px13_audio.py uninstall
```

If another fix existed before installation, rollback returns to that fix, not a pristine OS. The earlier manual repair described in the investigation used `/var/backups/px13-audio-before-repair`; that directory is independent of this installer's snapshot.

## Updates and reinstalling

The installer rejects a second installation while its snapshot exists, preventing the original backup from being overwritten. To change versions, uninstall, inspect the updated OS configuration, then install again.

If ALSA packages have updated since installation, uninstalling restores the old snapshot and may replace newer UCM content. Refresh the affected distribution package (`alsa-ucm-conf` on Ubuntu) before evaluating a clean upstream configuration or reinstalling. Do not blindly restore stale configuration over a newer package and assume it is current.
