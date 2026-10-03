"""Bounded main-study blocks with verified persistent backup before eviction.

The external upload command is a current library_upload.py helper. Its receipt
must explicitly acknowledge each archive. An uncertain write blocks resume.
Only local copies of archived heavy streams are removed; runs/checkpoints stay.
"""
import argparse,csv,hashlib,json,os,platform,subprocess,time,zipfile,shutil,tempfile
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from run_signed_social_pilot import worker,sha
from ena_abm.mechanism_experiment import ROOT,profiles,atomic_json,write_csv,verify_checkpoint,require_space

HEAVY=['events.jsonl.gz','ticks.jsonl.gz','initializations.jsonl.gz','final_states.jsonl.gz']

def staged_worker(payload):
    """Generate/verify outside synchronized workspace, then copy finalized files."""
    profile,destination,spec=payload
    temporary=Path(tempfile.mkdtemp(prefix='ena_signed_main_',dir='/tmp'))
    result=worker((profile,str(temporary),spec))
    source=temporary/profile['profile'];target=Path(destination)/profile['profile']
    checkpoint=json.loads((source/'checkpoint.json').read_text())
    verify_checkpoint(source,checkpoint)
    target.mkdir(exist_ok=False)
    for name in [*checkpoint['hashes'],'checkpoint.json']:
        shutil.copyfile(source/name,target/name)
    verify_checkpoint(target,checkpoint)
    shutil.rmtree(temporary)
    return result

def retained_check(root,checkpoint):
    for name in ['runs.jsonl.gz','paired_contrasts.csv']:
        assert sha(root/name)==checkpoint['hashes'][name],name

def package_profile(root,archive,checkpoint):
    verify_checkpoint(root,checkpoint)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for f in sorted(root.iterdir()):
            if f.is_file() and f.name!='backup_receipt.json':z.write(f,f.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in checkpoint['hashes'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
    return sha(archive)

def evict_backed(root,archive,receipt,checkpoint):
    if receipt.get('status')!='succeeded' or not receipt.get('library_file_id'):
        raise ValueError('No acknowledged persistent copy; refuse local eviction')
    if archive.exists():assert sha(archive)==receipt['archive_sha256']
    retained_check(root,checkpoint)
    for name in HEAVY:
        p=root/name
        if p.exists():
            assert sha(p)==checkpoint['hashes'][name]
            p.unlink()
    if archive.exists():archive.unlink()

def archive_block(out,ids,helper):
    stage=out/'archives';stage.mkdir(exist_ok=True)
    requests=[];metadata=[]
    for pid in ids:
        root=out/pid;cp=json.loads((root/'checkpoint.json').read_text())
        archive=stage/f'ENA_Inhibicion_Refuerzo_Principal_v0.1_{pid}.zip'
        if (root/'backup_receipt.json').exists():
            evict_backed(root,archive,json.loads((root/'backup_receipt.json').read_text()),cp)
            continue
        if (root/'upload_pending.json').exists():
            raise RuntimeError(f'Uncertain upload for {pid}; reconcile persistent receipt before retry')
        require_space(out,2.)
        digest=package_profile(root,archive,cp)
        metadata.append((pid,archive,digest))
        requests.append({'local_path':str(archive),'purpose':'create_library_file','library_artifact_type':'other'})
    if not requests:return
    for pid,archive,digest in metadata:
        atomic_json(out/pid/'upload_pending.json',{'archive':str(archive),'sha256':digest})
    call=subprocess.run(['python3',str(helper)],input=json.dumps({'uploads':requests}),
                        text=True,capture_output=True)
    # Persist the complete private helper output even on failure for reconciliation.
    batch=out/('upload_result_'+str(time.time_ns())+'.json')
    batch.write_text(call.stdout)
    if call.returncode:raise RuntimeError('Backup helper failed; originals retained: '+call.stderr[-400:])
    payload=json.loads(call.stdout.strip().splitlines()[-1]);items=payload['results']
    assert len(items)==len(metadata)
    for (pid,archive,digest),r in zip(metadata,items):
        assert r['local_path']==str(archive)
        if r.get('status')!='succeeded' or not r.get('library_file_id'):
            raise RuntimeError(f'Backup unconfirmed for {pid}; originals retained')
        receipt={**r,'archive_sha256':digest,'archive_bytes':archive.stat().st_size}
        atomic_json(out/pid/'backup_receipt.json',receipt)
        (out/pid/'upload_pending.json').unlink()
    # Eviction begins only after every receipt in the block has been persisted.
    for pid,archive,_ in metadata:
        root=out/pid
        evict_backed(root,archive,json.loads((root/'backup_receipt.json').read_text()),
                    json.loads((root/'checkpoint.json').read_text()))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    p.add_argument('--upload-helper',required=True);p.add_argument('--workers',type=int,default=6)
    p.add_argument('--block-size',type=int,default=6);p.add_argument('--resume',action='store_true')
    p.add_argument('--adopt-previous-output',help='Explicit operational revision; adopt only verified profiles with identical scientific source/configuration')
    a=p.parse_args();out=Path(a.output).resolve();helper=Path(a.upload_helper).resolve()
    assert 1<=a.workers<=6 and 1<=a.block_size<=6
    spec=json.loads((ROOT/'configs/signed_social_v0.1_main.json').read_text())
    assert spec['main_execution_enabled'] and spec['replicates']==400
    selected=profiles();assert len(selected)==96
    identity={'specification':spec,'source_sha256':{str(x.relative_to(ROOT)):sha(x) for x in sorted((ROOT/'src/ena_abm').glob('*.py'))},
        'worker_sha256':sha(ROOT/'scripts/run_signed_social_pilot.py'),'runner_sha256':sha(__file__),
        'profiles_sha256':sha(ROOT/'results/summaries/registered_profiles_v0.5.csv'),
        'python':platform.python_version()}
    if a.resume:assert json.loads((out/'execution_identity.json').read_text())==identity
    else:
        out.mkdir(parents=True,exist_ok=False);atomic_json(out/'execution_identity.json',identity)
        if a.adopt_previous_output:
            previous=Path(a.adopt_previous_output).resolve()
            old=json.loads((previous/'execution_identity.json').read_text())
            for key in ['specification','source_sha256','worker_sha256','profiles_sha256','python']:
                assert old[key]==identity[key],('scientific identity mismatch',key)
            adopted=[]
            for profile in selected:
                prior=previous/profile['profile']
                if not (prior/'checkpoint.json').exists():continue
                cp=json.loads((prior/'checkpoint.json').read_text())
                if (prior/'backup_receipt.json').exists():retained_check(prior,cp)
                else:verify_checkpoint(prior,cp)
                target=out/profile['profile'];target.mkdir()
                for name in [*cp['hashes'],'checkpoint.json','backup_receipt.json']:
                    if (prior/name).exists():shutil.copyfile(prior/name,target/name)
                retained_check(target,cp);adopted.append(profile['profile'])
            atomic_json(out/'operational_revision.json',{'previous_output':str(previous),
                'previous_identity_sha256':sha(previous/'execution_identity.json'),
                'adopted_verified_profiles':adopted,'scientific_source_and_configuration_unchanged':True,
                'change':'Generate and verify full trajectories in isolated /tmp before copying finalized files; previous outputs preserved'})
    write_csv(out/'profiles.csv',selected);start=time.perf_counter()
    for offset in range(0,96,a.block_size):
        block=selected[offset:offset+a.block_size];pending=[]
        for profile in block:
            root=out/profile['profile']
            if (root/'checkpoint.json').exists():
                cp=json.loads((root/'checkpoint.json').read_text())
                if (root/'backup_receipt.json').exists():retained_check(root,cp)
                else:verify_checkpoint(root,cp)
            else:
                if root.exists():
                    recovery=out/'recovery';recovery.mkdir(exist_ok=True)
                    root.rename(recovery/(profile['profile']+'-'+str(time.time_ns())))
                pending.append(profile)
        require_space(out,2.)
        if pending:
            with ProcessPoolExecutor(max_workers=a.workers) as pool:
                futures=[pool.submit(staged_worker,(profile,str(out),spec)) for profile in pending]
                for f in as_completed(futures):
                    r=f.result();print('Simulated',r['profile_id'],'8000 trajectories',flush=True)
        ids=[profile['profile'] for profile in block]
        print('Backing up block',offset//a.block_size+1,flush=True)
        archive_block(out,ids,helper)
        complete=len(list(out.glob('P*/backup_receipt.json')))
        atomic_json(out/'progress.json',{'profiles_backed_up':complete,'trajectories':complete*8000,
            'total_profiles':96,'elapsed_seconds_this_session':time.perf_counter()-start})
        print('BACKED_UP',complete,'/96',flush=True)
    rows=[];results=[];receipts=[]
    for profile in selected:
        root=out/profile['profile'];cp=json.loads((root/'checkpoint.json').read_text());retained_check(root,cp)
        results.append(cp['result']);receipts.append(json.loads((root/'backup_receipt.json').read_text()))
        with (root/'paired_contrasts.csv').open() as f:rows.extend(csv.DictReader(f))
    assert len(rows)==76800 and len({(r['profile_id'],r['replicate_id'],r['r']) for r in rows})==76800
    assert sum(x['files']['runs']['rows'] for x in results)==768000
    write_csv(out/'paired_contrasts.csv',rows)
    atomic_json(out/'manifest.json',{'status':'main_complete','trajectories':768000,'profiles':96,
        'replicates':400,'specification':spec,'per_profile':results,'persistent_backups':receipts,
        'elapsed_seconds_this_session':time.perf_counter()-start,'identity_sha256':sha(out/'execution_identity.json'),
        'paired_contrasts_sha256':sha(out/'paired_contrasts.csv')})
    print('MAIN COMPLETE: 768000 audited trajectories, 96 persistent archives',flush=True)

if __name__=='__main__':main()
