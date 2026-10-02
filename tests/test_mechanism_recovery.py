import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ena_abm.mechanism_experiment import (
    ROOT, atomic_json, profiles, require_space, run, verify_checkpoint,
)


class RecoveryTests(unittest.TestCase):
    def test_low_space_refuses_start(self):
        with patch('ena_abm.mechanism_experiment.shutil.disk_usage') as usage:
            usage.return_value.free = 4 * 2**30
            with self.assertRaises(RuntimeError):
                require_space(ROOT, 5)

    def test_interrupted_profile_recovery_matches_uninterrupted_data(self):
        selected = profiles()[:2]
        spec = json.loads((ROOT/'configs/mechanisms_v0.1.json').read_text())
        spec['pilot_profiles'] = [p['profile'] for p in selected]
        spec['pilot_replicates'] = 2
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root/'config.json'; atomic_json(config, spec)
            first = root/'first'; resumed = root/'resumed'
            with patch('ena_abm.mechanism_experiment.profiles', return_value=selected), patch(
                'ena_abm.mechanism_experiment.selected_pilot_profiles', return_value=spec['pilot_profiles']
            ):
                run(config, first, workers=1, minimum_free_gib=0, stop_free_gib=0)
                resumed.mkdir()
                import shutil
                shutil.copy(first/'execution_identity.json', resumed/'execution_identity.json')
                shutil.copy(first/'profiles.csv', resumed/'profiles.csv')
                shutil.copytree(first/selected[0]['profile'], resumed/selected[0]['profile'])
                incomplete=resumed/selected[1]['profile']; incomplete.mkdir()
                (incomplete/'trace.part').write_text('interrupted')
                run(config, resumed, workers=1, resume=True, minimum_free_gib=0, stop_free_gib=0)
            for profile in selected:
                for path in (first/profile['profile']).iterdir():
                    if path.name != 'checkpoint.json':
                        self.assertEqual(path.read_bytes(), (resumed/profile['profile']/path.name).read_bytes())
            self.assertEqual((first/'paired_contrasts.csv').read_bytes(), (resumed/'paired_contrasts.csv').read_bytes())
            self.assertTrue(list((resumed/'recovery').iterdir()))
            checkpoint=json.loads((resumed/selected[0]['profile']/'checkpoint.json').read_text())
            (resumed/selected[0]['profile']/'paired_contrasts.csv').write_text('corrupt')
            with self.assertRaises(ValueError):
                verify_checkpoint(resumed/selected[0]['profile'], checkpoint)
