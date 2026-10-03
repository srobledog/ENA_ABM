"""Run the 24,000-trajectory pilot; checkpoints per profile, full traces."""
import argparse
import hashlib
import json
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from ena_abm.mechanism_experiment import (ROOT, profiles, configuration, DeterministicWriter,
    emit, write_csv, atomic_json, verify_checkpoint, require_space)
from ena_abm.rng import stable_seed
from ena_abm.signed_social import SignedModel, signed_audit

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def worker(payload):
    p,out,spec=payload;root=Path(out)/p['profile'];root.mkdir(exist_ok=False)
    start=time.perf_counter();rows=[]
    writers={kind:DeterministicWriter(root/(kind+'.jsonl.gz')) for kind in
             ['runs','ticks','events','initializations','final_states']}
    for k in range(spec['replicates']):
        require_space(root,2.)
        seed=stable_seed(spec['experiment_seed'],spec['namespace'],p['profile'],k)
        common=configuration(p,replicate=k,master_seed=seed,strategy='direct')
        initial=SignedModel(common,social_mode='S')
        block={'protocol_version':'signed_social_v0.1','profile_id':p['profile'],
               'stage':'pilot','replicate_id':k,'master_seed':seed,
               'initialization_signature':initial.initialization_signature}
        writers['initializations'].write({**block,'configuration':common.to_dict(),
             'edges':initial.graph.edges(),'consumers':[asdict(c) for c in initial.consumers]})
        gaps={};ys={}
        for mode in spec['modes']:
            d=SignedModel(common,social_mode=mode);o=d.run();v=signed_audit(d,o)
            ys[('D',mode,None)]=o.summary['new_adoptions']
            emit(writers,{**block,'social_mode':mode},d,o,v,'D'+mode,None)
            for dest in ['L','A']:
                for r in spec['relative_costs']:
                    c=configuration(p,replicate=k,master_seed=seed,strategy='referral',cost=r)
                    m=SignedModel(c,social_mode=mode,destination_mode=dest)
                    z=m.run();v=signed_audit(m,z)
                    assert z.initialization_signature==initial.initialization_signature
                    ys[(dest,mode,r)]=z.summary['new_adoptions']
                    gaps[(dest,mode,r)]=z.summary['new_adoptions']-o.summary['new_adoptions']
                    emit(writers,{**block,'social_mode':mode},m,z,v,dest+mode,r)
        for r in spec['relative_costs']:
            g={m:gaps[('L',m,r)] for m in spec['modes']}
            row={'profile_id':p['profile'],'replicate_id':k,'r':r,
                 **{'G'+m:g[m] for m in spec['modes']},'BP':g['P']-g['Z'],
                 'BM':g['M']-g['Z'],'D_components':g['M']-g['P'],
                 'H':g['S']-g['P']-g['M']+g['Z']}
            for mode in spec['modes']:
                row['local_global_'+mode]=ys[('L',mode,r)]-ys[('A',mode,r)]
                row['absolute_local_'+mode]=ys[('L',mode,r)]-ys[('L','Z',r)]
                row['absolute_direct_'+mode]=ys[('D',mode,None)]-ys[('D','Z',None)]
            rows.append(row)
    files={kind:w.close() for kind,w in writers.items()}
    for kind,meta in files.items():
        f=root/(kind+'.jsonl.gz');meta.update(compressed_bytes=f.stat().st_size,sha256=sha(f))
    write_csv(root/'paired_contrasts.csv',rows)
    result={'profile_id':p['profile'],'replicates':spec['replicates'],
            'elapsed_seconds':time.perf_counter()-start,'files':files}
    checkpoint={'result':result,'hashes':{f.name:sha(f) for f in root.iterdir() if f.is_file()}}
    verify_checkpoint(root,checkpoint);atomic_json(root/'checkpoint.json',checkpoint)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    parser.add_argument('--resume',action='store_true');parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();out=Path(args.output)
    spec=json.loads((ROOT/'configs/signed_social_v0.1_pilot.json').read_text())
    identity={'specification':spec,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in
        sorted((ROOT/'src/ena_abm').glob('*.py'))},'runner_sha256':sha(__file__),'python':platform.python_version()}
    if args.resume:
        assert json.loads((out/'execution_identity.json').read_text())==identity
    else:
        out.mkdir(parents=True,exist_ok=False);atomic_json(out/'execution_identity.json',identity)
    selected=[next(p for p in profiles() if p['profile']==pid) for pid in spec['pilot_profiles']]
    write_csv(out/'profiles.csv',selected);results=[];pending=[];start=time.perf_counter()
    for p in selected:
        root=out/p['profile']
        if (root/'checkpoint.json').exists():results.append(verify_checkpoint(root,json.loads((root/'checkpoint.json').read_text())))
        else:
            if root.exists():
                recovery=out/'recovery';recovery.mkdir(exist_ok=True)
                root.rename(recovery/(p['profile']+'-'+str(time.time_ns())))
            pending.append(p)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(worker,(p,str(out),spec)) for p in pending]
        for f in as_completed(futures):
            r=f.result();results.append(r)
            atomic_json(out/'progress.json',{'complete':len(results),'total':12,'profiles':[x['profile_id'] for x in results]})
            print('Completed',r['profile_id'],len(results),'/12',flush=True)
    import csv
    rows=[]
    for p in selected:
        with (out/p['profile']/'paired_contrasts.csv').open() as f:rows.extend(csv.DictReader(f))
    write_csv(out/'paired_contrasts.csv',rows)
    assert len(rows)==2400 and sum(r['files']['runs']['rows'] for r in results)==24000
    atomic_json(out/'manifest.json',{'status':'technical_pilot_complete','profiles':12,'replicates':100,
        'trajectories':24000,'per_profile':results,'elapsed_seconds_this_session':time.perf_counter()-start,
        'specification':spec,'identity_sha256':sha(out/'execution_identity.json')})
    print('PILOT COMPLETE: 24000 audited trajectories',flush=True)

if __name__=='__main__':main()
