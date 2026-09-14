# Obtaining the firmware from ASUS

Use the **TI SmartAMP** audio driver for **HN7306EAC** from ASUS support. The package verified in this investigation was:

`SmartAMP_TI_DCH_TexasInstruments_Z_V6.3.1.15_47519.exe`

Official download:

[ASUS TI SmartAMP V6.3.1.15](https://dlcdnets.asus.com/pub/ASUS/nb/Image/Driver/Audio/47519/SmartAMP_TI_DCH_TexasInstruments_Z_V6.3.1.15_47519.exe?model=HN7306EAC)

```bash
curl -fL --proto '=https' --tlsv1.2 \
  'https://dlcdnets.asus.com/pub/ASUS/nb/Image/Driver/Audio/47519/SmartAMP_TI_DCH_TexasInstruments_Z_V6.3.1.15_47519.exe?model=HN7306EAC' \
  -o SmartAMP.exe
sudo apt install 7zip
bash scripts/extract-firmware.sh ./SmartAMP.exe ./firmware
```

`firmware` must be a new directory. The extractor verifies both files before creating it. Run extraction as your normal user. The Windows installer is never executed.

## Package layout discovered during the repair

The outer file is a PE executable. Force PE extraction to avoid 7-Zip automatically descending into its embedded installer:

```bash
7z x -tPE SmartAMP.exe -oouter
7z x outer/.rsrc/ZIP/103 -opayload
```

Despite the resource name `ZIP`, resource `103` is a **7z archive**. It contains the actual `Firmwares` directory:

```text
Firmwares/1714-1-0x8.bin
Firmwares/1714-1-0xB.bin
```

The other resource, `.rsrc/EXE/102`, is an Inno Setup executable. Extracting it produced installer helpers rather than the calibration files. Wine and Inno Setup extraction are unnecessary for the verified package.

## Verified firmware

Both files are 40,746 bytes.

| Extracted source | Linux name | SHA-256 |
| --- | --- | --- |
| `1714-1-0x8.bin` | `1714-1-8.bin` | `9a105de50978fc3250062d66bea6b77f3aaabaf85280739be28ff1ed3ae535ca` |
| `1714-1-0xB.bin` | `1714-1-B.bin` | `a975dc7e2340cb5c97259d5e8c3d7e447b5a0af1a91528c058c9fda0adeb74c1` |

The installer also writes the same bytes as `FFFF-1-8.bin` and `FFFF-1-B.bin`. These aliases match filenames explicitly requested by the tested kernel. They do not turn the firmware into a generic calibration for other laptops.

A different ASUS package may contain different valid firmware, but this installer intentionally rejects unverified checksums. Document and review a new package before changing the allowlist. Never substitute another laptop's calibration file just because its name looks similar.

## Distribution

Keep firmware and the downloaded installer out of commits and release archives. The repository's ignore rules exclude them. Download the proprietary files directly from ASUS for your own machine; no redistribution rights are asserted here.
