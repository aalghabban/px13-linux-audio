# Troubleshooting

Run diagnostics in your logged-in desktop session, as your normal user:

```bash
python3 scripts/px13_audio.py diagnose
```

If a restricted terminal cannot access PipeWire or ALSA devices, retry in a normal local terminal. A permission error or sandbox-specific `no soundcards found` is not evidence that the kernel failed to detect hardware.

## Dummy Output remains

```bash
cat /proc/asound/cards
wpctl status
journalctl -k --since '5 minutes ago' --no-pager -g 'tas2783|snd_pci_ps|soundwire'
```

| Observation | Next check |
| --- | --- |
| No `amd-soundwire` ALSA card | Controller discovery/recovery; inspect the recovery service log |
| TAS2783 status `UNATTACHED` | Controller re-enumeration; firmware copies alone cannot attach it |
| `Direct firmware load ... failed` | Exact requested filename and installed firmware checksum |
| `error playback without fw download` | Earlier firmware errors and attachment status in the same recovery attempt |
| Chips attached, firmware available, no Speaker route | UCM override and `tas2783.conf`; package updates may have replaced files |
| Speaker exists but sound is silent | Default route, mute/volume, app routing, active PCM state, new kernel errors |

## Check both chips

```bash
cat /sys/bus/soundwire/devices/sdw:0:1:0102:0000:01:8/status
cat /sys/bus/soundwire/devices/sdw:0:1:0102:0000:01:b/status
```

Both should read `Attached` after successful recovery. The recovery script accepts capitalization differences. It stops with an error if the expected devices do not attach.

## Trigger the installed recovery

```bash
sudo python3 /usr/local/lib/px13-linux-audio/px13_audio.py recover
```

Close calls first. If the command hangs in a kernel operation, do not start concurrent resets. Preserve the logs and use a normal reboot after saving work. A service timeout cannot reliably kill a process blocked in uninterruptible kernel sleep.

## Test playback

Use the Sound settings panel to select the speaker output and set a low comfortable volume. Play a familiar audio file, or use the desktop speaker test.

```bash
wpctl get-volume @DEFAULT_AUDIO_SINK@
cat /proc/asound/card1/pcm2p/sub0/status
cat /proc/asound/card1/pcm2p/sub0/hw_params
```

The `card1` path matches the recorded machine; card numbers may change. `RUNNING` confirms a hardware stream is active, not that the sound is audible. Confirm with your ears and check both channels.

## After reboot or sleep

```bash
systemctl is-enabled px13-audio-rebind.service px13-audio-resume.service
journalctl -b -u px13-audio-rebind.service --no-pager
journalctl -b -u px13-audio-resume.service --no-pager
```

Service enablement is not proof of a successful run. Check exit status, chip attachment, current kernel errors, and audible playback. Report cold boot and sleep recovery separately.

## Unsupported hardware or checksum

Do not remove the installer guard to force another model through. Open an issue with its DMI model, kernel, ALSA card/components, codec IDs, exact firmware requests, and test results. A model-specific calibration must not be guessed from a similar product name.

## What to share

Use the issue template. Share a short log excerpt around the failed attempt, not an entire system journal. Review diagnostics for user names, host names, and unrelated device information before publishing. Do not attach proprietary firmware or the ASUS executable.
