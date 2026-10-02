"""Verify final published data, independent of clocks and temporary work files."""
import argparse,gzip,hashlib,json
from pathlib import Path

def checked_files(root):
    manifest=json.loads((root/'manifest.json').read_text())
    published={k:v for k,v in manifest['full_data_sha256'].items() if not k.endswith('.part')}
    for name,expected in published.items():
        path=root/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,('compressed or CSV hash',name)
    for profile in manifest['per_profile']:
        for kind,metadata in profile['files'].items():
            path=root/profile['profile_id']/(kind+'.jsonl.gz')
            digest=hashlib.sha256();length=0
            with gzip.open(path,'rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):
                    digest.update(chunk);length+=len(chunk)
            assert digest.hexdigest()==metadata['content_sha256']
            assert length==metadata['uncompressed_bytes']
    return manifest,published

p=argparse.ArgumentParser()
p.add_argument('--first',required=True);p.add_argument('--second',required=True);p.add_argument('--output',required=True)
a=p.parse_args()
x,h1=checked_files(Path(a.first));y,h2=checked_files(Path(a.second))
assert h1==h2 and x['specification']==y['specification'] and x['unique_trajectories']==y['unique_trajectories']
report={'status':'passed','datasets_identical':len(h1),'trajectories_each_execution':x['unique_trajectories'],
    'execution_commit':x['extension_commit'],'both_final_gzip_crc_and_logical_hashes_verified':True,
    'all_data_sha256':h1,'excluded':['manifest.json','unpublished .part temporary files']}
Path(a.output).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS:',len(h1),'published files exactly reproduced')
