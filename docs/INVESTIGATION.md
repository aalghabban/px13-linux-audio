# Investigation: Dummy Output to working speakers

## Initial observations

On Ubuntu 26.04 with kernel `7.0.0-14-generic`, PipeWire and WirePlumber were running. The only playback sink was `Dummy Output`, at volume 1.00 and not muted. ALSA exposed the AMD SoundWire card, including:

```text
SDW1-PIN0-PLAYBACK-SimpleJack rt721-sdca-aif1-0
SDW1-PIN1-PLAYBACK-SmartAmp multicodec-2
```

The card components were:

```text
cfg-amp:2 hs:rt721
```

There was no speaker codec token. PipeWire initially offered an unavailable HiFi profile with headphones/headset routes but no speaker route. Its active profile was Off.

The kernel repeatedly reported:

```text
slave-tas2783 ... error playback without fw download
slave-tas2783 ... ASoC error (-22): at snd_soc_dai_hw_params() on tas2783-codec
```

The installed firmware tree contained other TAS2783 firmware, but not the ASUS `1714` files. The stock RT721 UCM file also contained `Headphone Switch` commands identified in the earlier model-specific repair as unsupported.

## First repair: firmware and UCM

The official ASUS V6.3.1.15 package was downloaded. Its two `1714` firmware files matched the published checksums. They were installed along with a TAS2783 speaker device and a model-specific UCM override. The two unavailable headphone switch commands were removed.

A driver unbind/bind was then attempted on `0000:c4:00.5`.

**Result:** Dummy Output remained. Both amplifiers reported `UNATTACHED`. The journal included:

```text
snd_pci_ps 0000:c4:00.5: AMD-Vi: Event logged [IO_PAGE_FAULT ...]
```

The firmware was present on disk, but the device was not ready to consume it. Merely repeating the same driver restart was not sufficient in this session.

## Second repair: PCI removal and rescan

The audio PCI function was removed through its sysfs `remove` file. After a short delay, PCI was rescanned. Both amplifier status files changed to `Attached`.

This is distinct from driver unbind/bind: the PCI device itself is re-enumerated. Only the audio function was removed; the rescan performs PCI discovery.

**Result:** hardware attachment recovered, but playback still failed. The now-attached drivers reported more specific firmware requests:

```text
Direct firmware load for FFFF-1-8.bin failed with error -2
Failed to read fw binary FFFF-1-8.bin
Direct firmware load for FFFF-1-B.bin failed with error -2
Failed to read fw binary FFFF-1-B.bin
```

Before PCI re-enumeration, the subsystem device read `0x1714`. A later read during repository validation, after successful recovery, returned `0xffff`; vendor/device remained `0x1022:0x15e2`. The reason the subsystem value changed was **not established**. The observation supports a filename workaround; it does not establish a particular driver source-code defect.

## Third repair: names matching the kernel request

Copies of the verified ASUS firmware were installed as:

```text
/lib/firmware/FFFF-1-8.bin
/lib/firmware/FFFF-1-B.bin
```

The original `1714` filenames were retained. The audio PCI function was re-enumerated again, and user audio services restarted.

**Result:** PipeWire exposed `Audio Coprocessor Speaker` as the default output. The running browser stream was routed to `Speaker:playback_FL` and `Speaker:playback_FR`. ALSA reported:

```text
state: RUNNING
format: S16_LE
channels: 2
rate: 48000 (48000/1)
```

No new matching driver errors appeared during the final 30-second observation, and the laptop owner confirmed audible sound.

## Conclusions and limits

The observed failure involved three separate layers: device attachment, firmware loading, and the userspace speaker route. Check each layer rather than assuming Dummy Output means the audio service is stopped.

Boot and post-sleep recovery were enabled, but neither reboot nor suspend/resume was tested after the final repair. Headphones, headset microphone, HDMI, and built-in microphone behavior were not audibly tested. Their appearance in a device list is not a functional test.

This repository's new installer was developed after the manual repair. Automated tests and a hardware dry run validate parts of its packaging; they do not establish a clean-install or persistence result.
