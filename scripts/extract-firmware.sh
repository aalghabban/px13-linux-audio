#!/usr/bin/env bash
# Extract data from ASUS's wrapper; do not execute its Windows programs.
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "Usage: $0 /path/to/ASUS-SmartAMP.exe /path/to/new-output-directory" >&2
  exit 2
fi
archive_tool=$(command -v 7z || command -v 7zz || true)
[[ -n "$archive_tool" ]] || { echo 'Install 7zip first.' >&2; exit 1; }
[[ -f "$1" && ! -e "$2" ]] || { echo 'Installer must exist and output directory must be new.' >&2; exit 1; }
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
"$archive_tool" x -tPE "$1" "-o$work/outer" >/dev/null
payload="$work/outer/.rsrc/ZIP/103"
[[ -f "$payload" ]] || { echo 'Unexpected ASUS package layout; see docs/FIRMWARE.md.' >&2; exit 1; }
"$archive_tool" x "$payload" "-o$work/payload" >/dev/null
python3 - "$work/payload/Firmwares" "$2" <<'PY'
import hashlib
from pathlib import Path
import sys
hashes = {'8': '9a105de50978fc3250062d66bea6b77f3aaabaf85280739be28ff1ed3ae535ca',
          'B': 'a975dc7e2340cb5c97259d5e8c3d7e447b5a0af1a91528c058c9fda0adeb74c1'}
data = {}
for amp, expected in hashes.items():
    blob = (Path(sys.argv[1]) / f'1714-1-0x{amp}.bin').read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected:
        raise SystemExit(f'Unexpected firmware checksum for amplifier {amp}; no output written.')
    data[amp] = blob
output = Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=False)
for amp, blob in data.items():
    (output / f'1714-1-{amp}.bin').write_bytes(blob)
print(f'Extracted and verified both firmware files in {output}')
PY
