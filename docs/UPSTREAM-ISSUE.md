# Draft upstream report

This is a draft, not a submitted issue. Firmware distribution, ALSA UCM, and kernel attachment behavior may need separate reports to their respective maintainers.

## Suggested title

ASUS ProArt PX13 HN7306EAC: TAS2783 speakers silent, missing UCM route, FFFF firmware requests, and SoundWire attachment failure

## Environment

- Ubuntu 26.04 LTS
- Linux 7.0.0-14-generic
- PipeWire 1.6.2
- alsa-ucm-conf 1.2.15.3-1ubuntu1
- linux-firmware 20260319.git217ca6e4.1ubuntu
- ASUS ProArt PX13 HN7306EAC
- AMD audio controller 0000:c4:00.5, subsystem device 0x1714
- snd_pci_ps / snd_acp_sdw_legacy_mach
- RT721 headset and two TAS2783 amplifiers
- ALSA components: `cfg-amp:2 hs:rt721`

## Expected behavior

Internal speakers appear as a usable output and play stereo audio.

## Observed behavior

PipeWire and WirePlumber were running, but only Dummy Output was usable. Kernel logs repeatedly showed TAS2783 playback attempts without firmware download. The stock UCM setup exposed headset routes but no speaker route.

After installing exact ASUS calibration and a local UCM correction, driver unbind/bind left both amplifier devices UNATTACHED, with an AMD-Vi IO_PAGE_FAULT. Audio PCI removal/rescan restored Attached status.

The driver then requested `FFFF-1-8.bin` and `FFFF-1-B.bin`, while the pre-recovery PCI subsystem device had read 0x1714. A later post-recovery read returned 0xffff with vendor/device still 0x1022:0x15e2. Installing the verified ASUS calibration under those names, followed by audio PCI re-enumeration and audio service restart, restored confirmed audible playback.

## Relevant excerpts

```text
error playback without fw download
ASoC error (-22): at snd_soc_dai_hw_params() on tas2783-codec
Direct firmware load for FFFF-1-8.bin failed with error -2
Direct firmware load for FFFF-1-B.bin failed with error -2
```

## Workaround and validation

- ASUS TI SmartAMP V6.3.1.15 package, firmware checksums recorded in FIRMWARE.md.
- Local TAS2783 UCM Speaker definition, PCM 2, stereo.
- HN7306EAC override selects tas2783 because the card components lack a speaker codec token.
- Remove unsupported `Headphone Switch` UCM cset commands.
- Supply both `1714` and observed `FFFF` firmware names.
- Remove/rescan the audio PCI function instead of only unbinding/rebinding the driver.
- Default Speaker sink appeared; browser stream routed to it; ALSA running at 48 kHz stereo S16_LE; audible output confirmed.

## Open questions

1. Why does the subsystem device change from 0x1714 to 0xffff after recovery, resulting in FFFF firmware requests?
2. Should the machine driver expose an explicit TAS2783 speaker component?
3. What upstream UCM changes are appropriate for this codec combination?
4. Can attachment recover without PCI removal/rescan?
5. Can the matching ASUS calibration be included in an upstream firmware distribution?

Reboot and suspend/resume after the final workaround have not been tested. This report does not establish a regression range, a reproducible suspend trigger, or behavior on a newer kernel. Those details should be added only after testing.
