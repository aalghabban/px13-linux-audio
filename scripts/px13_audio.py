#!/usr/bin/env python3
"""Narrowly scoped ASUS HN7306EAC speaker repair and rollback utility."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PCI = '0000:c4:00.5'
MODEL = 'ProArt PX13 HN7306EAC'
CARD = 'ASUSTeKCOMPUTERINC.-ProArtPX13HN7306EAC-1.0-HN7306EAC'
UCM = Path('/usr/share/alsa/ucm2')
STATE = Path('/var/lib/px13-linux-audio')
INSTALLED = Path('/usr/local/lib/px13-linux-audio/px13_audio.py')
UNITS = ('px13-audio-rebind.service', 'px13-audio-resume.service')
HASHES = {
    '8': '9a105de50978fc3250062d66bea6b77f3aaabaf85280739be28ff1ed3ae535ca',
    'B': 'a975dc7e2340cb5c97259d5e8c3d7e447b5a0af1a91528c058c9fda0adeb74c1',
}


def run(args, check=True, timeout=30):
    return subprocess.run(args, text=True, capture_output=True, check=check, timeout=timeout)


def read(path):
    return Path(path).read_text().strip()


def require_root():
    if os.geteuid() != 0:
        raise RuntimeError('Use sudo for this command. Diagnose and dry-run need no sudo.')


def hardware_check():
    model = read('/sys/class/dmi/id/product_name')
    if model != MODEL:
        raise RuntimeError(f'Unsupported model: {model}. Only {MODEL} is validated.')
    device = Path('/sys/bus/pci/devices') / PCI
    if device.exists():
        if (read(device / 'vendor') != '0x1022' or read(device / 'device') != '0x15e2'
                or read(device / 'subsystem_device') not in ('0x1714', '0xffff')):
            raise RuntimeError('Audio PCI IDs do not match the validated hardware.')
        driver = device / 'driver'
        if not driver.exists() or driver.resolve().name != 'snd_pci_ps':
            raise RuntimeError('Expected snd_pci_ps audio driver is not bound.')
    return device


def validate_firmware(directory):
    result = {}
    for amp, digest in HASHES.items():
        candidates = [directory / f'1714-1-{amp}.bin', directory / f'1714-1-0x{amp}.bin']
        source = next((p for p in candidates if p.is_file()), None)
        if source is None:
            raise RuntimeError(f'Missing ASUS firmware for amplifier {amp}. See docs/FIRMWARE.md.')
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError(f'Checksum mismatch: {source}. Expected the documented ASUS package.')
        result[amp] = data
    return result


def patch_rt721(text):
    # Keep upstream content intact except the two controls absent on this machine.
    return re.sub(r'^\s*cset "name=\x27Headphone Switch\x27 (?:on|off)"\s*$', '', text, flags=re.M)


def unit_text(resume=False):
    after = ('suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target'
             if resume else 'sound.target')
    wanted = after if resume else 'multi-user.target'
    delay = 'ExecStartPre=/bin/sleep 3\n' if resume else ''
    return (f'[Unit]\nDescription=ASUS PX13 speaker recovery\nAfter={after}\n'
            f'\n[Service]\nType=oneshot\nTimeoutStartSec=120\n{delay}'
            f'ExecStart=/usr/bin/python3 {INSTALLED} recover\n'
            f'\n[Install]\nWantedBy={wanted}\n')


def plan_install(firmware):
    generic = UCM / 'conf.d/amd-soundwire/amd-soundwire.conf'
    rt721 = UCM / 'sof-soundwire/rt721.conf'
    base = generic.read_text()
    if 'SpeakerCodec1' not in base or not rt721.is_file():
        raise RuntimeError('Unexpected ALSA UCM layout; refusing to overwrite it.')
    # Build the machine override from the installed upstream version.
    override = base + '\n# Local HN7306EAC TAS2783 speaker selection.\nDefine.SpeakerCodec1 "tas2783"\n'
    speaker = ('# HN7306EAC: TAS2783 SmartAmp is playback PCM 2.\n'
               'SectionDevice."Speaker" {\n Comment "Speaker"\n Value {\n'
               '  PlaybackPriority 100\n  PlaybackPCM "hw:${CardId},2"\n'
               '  PlaybackChannels 2\n }\n}\n')
    files = {
        UCM / f'conf.d/amd-soundwire/{CARD}.conf': override.encode(),
        UCM / 'sof-soundwire/tas2783.conf': speaker.encode(),
        rt721: patch_rt721(rt721.read_text()).encode(),
        INSTALLED: Path(__file__).read_bytes(),
    }
    for amp, data in firmware.items():
        # FFFF is an observed kernel request, not a claim about its root cause.
        for name in (f'1714-1-{amp}.bin', f'FFFF-1-{amp}.bin'):
            files[Path('/lib/firmware') / name] = data
    for unit in UNITS:
        files[Path('/etc/systemd/system') / unit] = unit_text('resume' in unit).encode()
    return files


def snapshot(files):
    if (STATE / 'manifest.json').exists():
        raise RuntimeError('An installation snapshot already exists. Uninstall before reinstalling.')
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if STATE.is_symlink() or STATE.stat().st_uid != 0:
        raise RuntimeError('State directory must be a root-owned real directory.')
    manifest = {'files': [], 'units': {}}
    for unit in UNITS:
        status = run(['systemctl', 'is-enabled', unit], check=False).stdout.strip()
        if status in ('masked', 'masked-runtime', 'enabled-runtime', 'linked', 'linked-runtime'):
            raise RuntimeError(f'Unsupported existing service state: {unit}: {status}')
        manifest['units'][unit] = status
    for i, target in enumerate(files):
        if target.is_symlink():
            raise RuntimeError(f'Refusing to replace symlink: {target}')
        entry = {'path': str(target), 'existed': target.exists()}
        if target.exists():
            entry['backup'] = str(i)
            shutil.copy2(target, STATE / str(i))
        manifest['files'].append(entry)
    (STATE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def install(directory, dry_run):
    hardware_check()
    if Path('/usr/lib/systemd/system-sleep/px13-audio-resume.sh').exists() or Path('/usr/lib/systemd/system-sleep/50-px13-soundwire').exists():
        raise RuntimeError('An older sleep hook exists. Resolve it using docs/INSTALL.md before installing.')
    files = plan_install(validate_firmware(directory))
    print('Files to install:')
    for target in files:
        print(f'  {target}')
    print('Services to enable:', ', '.join(UNITS))
    if dry_run:
        print('Dry run: firmware and hardware checks passed; no files changed.')
        return
    require_root()
    snapshot(files)
    try:
        for target, data in files.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o644)
        run(['systemctl', 'daemon-reload'])
        run(['systemctl', 'enable', *UNITS])
    except Exception:
        print('Install failed. Restoring the pre-install snapshot.', file=sys.stderr)
        uninstall()
        raise
    print('Installed. Run: sudo python3 ' + str(INSTALLED) + ' recover')
    print('Installation alone does not prove playback, reboot, or sleep recovery.')


def uninstall():
    require_root()
    manifest = json.loads((STATE / 'manifest.json').read_text())
    # Preserve any original service enablement, including an earlier PX13 repair.
    run(['systemctl', 'disable', *UNITS], check=False)
    for entry in reversed(manifest['files']):
        target = Path(entry['path'])
        if entry['existed']:
            shutil.copy2(STATE / entry['backup'], target)
        else:
            target.unlink(missing_ok=True)
    run(['systemctl', 'daemon-reload'])
    for unit, status in manifest['units'].items():
        if status == 'enabled':
            run(['systemctl', 'enable', unit])
    archive = STATE.with_name(STATE.name + '-restored-' + str(time.time_ns()))
    STATE.rename(archive)
    print(f'Original files restored. Snapshot retained at {archive}.')
    print('Reboot when convenient to clear firmware already loaded in the device.')


def refresh_users():
    result = run(['loginctl', 'list-users', '--no-legend'], check=False)
    for line in result.stdout.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        uid = fields[0]
        runtime = Path('/run/user') / uid
        if not (runtime / 'bus').exists():
            continue
        events = Path(f'/sys/fs/cgroup/user.slice/user-{uid}.slice/cgroup.events')
        if events.exists() and 'frozen 1' in events.read_text():
            print(f'Skipping frozen user session {uid}; device discovery resumes on thaw.')
            continue
        import pwd
        name = pwd.getpwuid(int(uid)).pw_name
        result = run(['runuser', '-u', name, '--', 'env', f'XDG_RUNTIME_DIR={runtime}',
                      'systemctl', '--user', 'restart', 'pipewire', 'pipewire-pulse', 'wireplumber'], check=False)
        if result.returncode:
            print(f'Audio service refresh failed for uid {uid}: {result.stderr.strip()}')


def recover():
    require_root()
    device = hardware_check()
    import fcntl
    with open('/run/px13-linux-audio.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print('Re-enumerating the audio PCI function only.', flush=True)
        if device.exists():
            (device / 'remove').write_text('1\n')
            time.sleep(2)
        # Linux PCI sysfs rescan discovers devices; it does not remove other functions.
        Path('/sys/bus/pci/rescan').write_text('1\n')
        for _ in range(40):
            if 'amd-soundwire' in read('/proc/asound/cards'):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError('amd-soundwire did not return after rescan.')
        expected = [Path('/sys/bus/soundwire/devices') / f'sdw:0:1:0102:0000:01:{amp}/status' for amp in ('8', 'b')]
        for _ in range(40):
            if all(p.exists() and read(p).lower() == 'attached' for p in expected):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError('Speaker chips remain unattached; see docs/TROUBLESHOOTING.md.')
        time.sleep(2)
        refresh_users()
        print('Both amplifiers attached. Check wpctl status and audible playback in your user session.')


def diagnose():
    for label, path in [('Model', '/sys/class/dmi/id/product_name'), ('OS', '/etc/os-release'),
                        ('ALSA cards', '/proc/asound/cards')]:
        print(f'\n{label}:\n{read(path)}')
    print('\nKernel:', os.uname().release)
    for path in sorted(Path('/sys/bus/soundwire/devices').glob('*/status')):
        print(path.parent.name, read(path))
    for command in [['wpctl', 'status'], ['aplay', '-l'], ['systemctl', 'is-enabled', *UNITS],
                    ['journalctl', '-k', '-b', '--no-pager', '-n', '30', '-g', 'tas2783|snd_pci_ps|soundwire']]:
        print('\n$', ' '.join(command))
        try:
            r = run(command, check=False)
            print(r.stdout, r.stderr)
        except (OSError, subprocess.SubprocessError) as exc:
            print(str(exc))
    print('Review output for host/user names before sharing it publicly.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('diagnose')
    commands.add_parser('recover')
    commands.add_parser('uninstall')
    install_parser = commands.add_parser('install')
    install_parser.add_argument('--firmware-dir', type=Path, required=True)
    install_parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'install':
            install(args.firmware_dir, args.dry_run)
        else:
            globals()[args.command]()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
