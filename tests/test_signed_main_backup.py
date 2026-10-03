import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_signed_social_main import worker,archive_block,evict_backed,sha
from ena_abm.mechanism_experiment import profiles

class BackupTests(unittest.TestCase):
    def test_backup_before_eviction_and_uncertain_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);profile=profiles()[0]
            spec={'replicates':1,'experiment_seed':2026100301,'namespace':'signed_main_backup_test',
                  'stage':'main','modes':['S','P','M','Z'],'relative_costs':[1.,1.2]}
            result=worker((profile,str(out),spec));root=out/profile['profile']
            self.assertEqual(result['files']['runs']['rows'],20)
            cp=json.loads((root/'checkpoint.json').read_text())
            with self.assertRaises(ValueError):evict_backed(root,out/'absent.zip',{},cp)
            self.assertTrue((root/'events.jsonl.gz').exists())
            (root/'upload_pending.json').write_text('{}')
            with self.assertRaises(RuntimeError):archive_block(out,[profile['profile']],Path('unused'))
            (root/'upload_pending.json').unlink()
            def fake_run(command,*,input,text,capture_output):
                req=json.loads(input)['uploads'][0]
                self.assertTrue((root/'events.jsonl.gz').exists())
                self.assertTrue(Path(req['local_path']).exists())
                class Result:pass
                r=Result();r.returncode=0;r.stderr='';r.stdout=json.dumps({'results':[
                    {'status':'succeeded','library_file_id':'TEST_ONLY_RECEIPT',
                     'local_path':req['local_path']} ]})
                return r
            with patch('run_signed_social_main.subprocess.run',side_effect=fake_run):
                archive_block(out,[profile['profile']],Path('unused'))
            self.assertFalse((root/'events.jsonl.gz').exists())
            self.assertTrue((root/'runs.jsonl.gz').exists())
            self.assertEqual(sha(root/'runs.jsonl.gz'),cp['hashes']['runs.jsonl.gz'])
            # Idempotent resume must not upload the acknowledged archive again.
            with patch('run_signed_social_main.subprocess.run',side_effect=AssertionError('duplicate write')):
                archive_block(out,[profile['profile']],Path('unused'))
