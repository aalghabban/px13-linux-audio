import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('repair', Path(__file__).parents[1] / 'scripts/px13_audio.py')
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


class RepairTests(unittest.TestCase):
    def test_wrong_model_is_rejected_before_pci_access(self):
        with patch.object(repair, 'read', return_value='Different laptop'):
            with self.assertRaisesRegex(RuntimeError, 'Unsupported model'):
                repair.hardware_check()

    def test_firmware_missing_and_corrupt_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with self.assertRaisesRegex(RuntimeError, 'Missing ASUS'):
                repair.validate_firmware(path)
            (path / '1714-1-8.bin').write_bytes(b'wrong calibration')
            with self.assertRaisesRegex(RuntimeError, 'Checksum mismatch'):
                repair.validate_firmware(path)

    def test_exact_hashes_accept_both_source_filename_styles(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            blobs = {'8': b'test left', 'B': b'test right'}
            (path / '1714-1-0x8.bin').write_bytes(blobs['8'])
            (path / '1714-1-B.bin').write_bytes(blobs['B'])
            hashes = {k: hashlib.sha256(v).hexdigest() for k, v in blobs.items()}
            with patch.object(repair, 'HASHES', hashes):
                self.assertEqual(repair.validate_firmware(path), blobs)

    def test_rt721_patch_preserves_other_controls_and_is_idempotent(self):
        source = '''SectionDevice."Headphones" {
 EnableSequence [
  cset "name='Headphone Switch' on"
  cset "name='Another Switch' on"
 ]
 DisableSequence [
  cset "name='Headphone Switch' off"
 ]
}
'''
        result = repair.patch_rt721(source)
        self.assertNotIn("name='Headphone Switch'", result)
        self.assertIn("name='Another Switch' on", result)
        self.assertEqual(repair.patch_rt721(result), result)

    def test_plan_installs_identical_aliases_and_local_override(self):
        with tempfile.TemporaryDirectory() as folder:
            ucm = Path(folder)
            (ucm / 'conf.d/amd-soundwire').mkdir(parents=True)
            (ucm / 'sof-soundwire').mkdir()
            (ucm / 'conf.d/amd-soundwire/amd-soundwire.conf').write_text('Syntax 7\nDefine.SpeakerCodec1 ""\n')
            (ucm / 'sof-soundwire/rt721.conf').write_text('# original\n')
            with patch.object(repair, 'UCM', ucm):
                files = repair.plan_install({'8': b'left', 'B': b'right'})
            self.assertEqual(files[Path('/lib/firmware/FFFF-1-8.bin')], b'left')
            self.assertEqual(files[Path('/lib/firmware/1714-1-B.bin')], b'right')
            override = files[ucm / f'conf.d/amd-soundwire/{repair.CARD}.conf']
            self.assertIn(b'Define.SpeakerCodec1 "tas2783"', override)

    def test_resume_unit_is_after_sleep_targets(self):
        text = repair.unit_text(True)
        self.assertIn('After=suspend.target', text)
        self.assertIn('TimeoutStartSec=120', text)
        self.assertIn('px13_audio.py recover', text)

    def test_snapshot_and_rollback_restore_bytes_modes_and_enablement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / 'existing.conf'
            old.write_bytes(b'original')
            old.chmod(0o640)
            new = root / 'added.bin'
            state = root / 'state'
            calls = []

            def fake_run(args, **kwargs):
                calls.append(args)
                status = 'enabled\n' if args[1] == 'is-enabled' and args[-1] == repair.UNITS[0] else 'disabled\n'
                return subprocess.CompletedProcess(args, 0, status, '')

            with patch.object(repair, 'STATE', state), patch.object(repair.os, 'geteuid', return_value=0), patch.object(repair, 'run', side_effect=fake_run):
                # Ownership check is separately enforced in production; test temp dir belongs to this user.
                real_stat = Path.stat
                from types import SimpleNamespace
                def stat_with_test_owner(path, *args, **kwargs):
                    stat = real_stat(path, *args, **kwargs)
                    if path == state and not kwargs.get('follow_symlinks') is False:
                        return SimpleNamespace(st_uid=0)
                    return stat
                with patch.object(Path, 'stat', stat_with_test_owner):
                    repair.snapshot({old: b'changed', new: b'new'})
                old.write_bytes(b'changed')
                old.chmod(0o644)
                new.write_bytes(b'new')
                repair.uninstall()
            self.assertEqual(old.read_bytes(), b'original')
            self.assertEqual(old.stat().st_mode & 0o777, 0o640)
            self.assertFalse(new.exists())
            self.assertIn(['systemctl', 'enable', repair.UNITS[0]], calls)
            self.assertNotIn(['systemctl', 'enable', repair.UNITS[1]], calls)
            self.assertFalse(state.exists())

    def test_dry_run_never_snapshots_or_writes(self):
        with patch.object(repair, 'hardware_check'), patch.object(repair, 'validate_firmware', return_value={}), patch.object(repair, 'plan_install', return_value={Path('/test/firmware'): b'x'}), patch.object(repair, 'snapshot') as snapshot, patch.object(repair.Path, 'exists', return_value=False):
            repair.install(Path('/unused'), True)
            snapshot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
