# Sources and attribution

The investigation built on prior public work and then verified the steps on the hardware documented here.

- [brainchillz/asus-proart-px13-linux-speaker-fix](https://github.com/brainchillz/asus-proart-px13-linux-speaker-fix): model-specific firmware, UCM, and recovery background. Source inspected at commit `e13b427143b0ed6bd861f048afbbca4aa751e956`. The manual repair initially used its configuration and recovery approach. The executable packaging in this repository is newly written.
- [namithj/Asus-ProArt-PX13-Linux-Mint-OR-Ubuntu-Speaker-Fix](https://github.com/namithj/Asus-ProArt-PX13-Linux-Mint-OR-Ubuntu-Speaker-Fix): documented PCI removal/rescan when unbind/bind leaves SoundWire peripherals unattached. That distinction was confirmed during this repair.
- [Official ASUS TI SmartAMP download](https://dlcdnets.asus.com/pub/ASUS/nb/Image/Driver/Audio/47519/SmartAMP_TI_DCH_TexasInstruments_Z_V6.3.1.15_47519.exe?model=HN7306EAC): source of the two calibration files; proprietary content is not redistributed here.
- [ALSA UCM configuration project](https://github.com/alsa-project/alsa-ucm-conf): upstream configuration. The installer reads the existing distribution files and makes a local model-specific adaptation. Upstream file licenses continue to apply.
- [Linux PCI sysfs documentation](https://docs.kernel.org/PCI/sysfs-pci.html): reference for PCI device access through sysfs.

The observed FFFF filename requests, successful firmware aliases, direct extraction through the ASUS PE resource, live playback state, and user confirmation are recorded in [INVESTIGATION.md](INVESTIGATION.md). They are observations from this case, not guarantees for all machines.
