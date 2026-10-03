"""Registered fixed-profile, paired-block bootstrap for signed-social main."""
import argparse,csv,gzip,hashlib,json,os
from collections import defaultdict
from pathlib import Path
import numpy as np

PRIMARY=['GP','BP','BM','D_components']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def classification(lo,hi,margin=.5):
    if lo>margin:return 'positive_beyond_diagnostic_margin'
    if hi<-margin:return 'negative_beyond_diagnostic_margin'
    if lo>=-margin and hi<=margin:return 'within_diagnostic_equivalence_margin'
    if lo>0 or hi<0:return 'sign_supported_relevance_uncertain'
    return 'inconclusive'

def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args()
    src=Path(a.source);out=Path(a.output);out.mkdir(exist_ok=False,parents=True)
    manifest=json.loads((src/'manifest.json').read_text())
    assert manifest['status']=='main_complete' and manifest['trajectories']==768000
    assert len(manifest['persistent_backups'])==96
    assert all(r['status']=='succeeded' and r['library_file_id'] for r in manifest['persistent_backups'])
    assert sha(src/'paired_contrasts.csv')==manifest['paired_contrasts_sha256']
    with (src/'paired_contrasts.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==76800
    names=[k for k in rows[0] if k not in ['profile_id','replicate_id','r']]
    ids=sorted({r['profile_id'] for r in rows});assert len(ids)==96
    lookup={(r['profile_id'],int(r['replicate_id']),float(r['r'])):r for r in rows}
    assert len(lookup)==76800
    data=np.array([[[[float(lookup[(pid,k,r)][n]) for n in names] for r in [1.,1.2]]
                    for k in range(400)] for pid in ids])
    assert data.shape==(96,400,2,len(names)) and np.isfinite(data).all()
    nidx={n:i for i,n in enumerate(names)}
    assert np.array_equal(data[:,:,:,nidx['BP']],data[:,:,:,nidx['GP']]-data[:,:,:,nidx['GZ']])
    assert np.array_equal(data[:,:,:,nidx['BM']],data[:,:,:,nidx['GM']]-data[:,:,:,nidx['GZ']])
    assert np.array_equal(data[:,:,:,nidx['D_components']],data[:,:,:,nidx['BM']]-data[:,:,:,nidx['BP']])
    assert np.array_equal(data[:,:,:,nidx['H']],data[:,:,:,nidx['GS']]-data[:,:,:,nidx['GP']]-data[:,:,:,nidx['GM']]+data[:,:,:,nidx['GZ']])
    # Independently reconstruct all gaps from raw run summaries; check source hashes.
    process=defaultdict(list);seen=set()
    for entry in sorted(manifest['per_profile'],key=lambda x:x['profile_id']):
        pid=entry['profile_id'];path=src/pid/'runs.jsonl.gz'
        assert sha(path)==entry['files']['runs']['sha256']
        block={}
        with gzip.open(path,'rt') as f:
            for line in f:
                r=json.loads(line);assert r['stage']=='main'
                key=(r['profile_id'],r['replicate_id'],r['arm'],r['relative_cost'])
                assert key not in seen;seen.add(key)
                block[(r['replicate_id'],r['arm'],r['relative_cost'])]=r['summary']['new_adoptions']
                z=r['audit'];s=r['summary']
                assert z['unique_exposed']+z['repeat_exposures']==s['exposures_delivered']
                vals={n:s[n] for n in ['new_adoptions','exposures_delivered','evaluation_events']}
                vals.update({n:z[n] for n in ['unique_exposed','repeat_exposures','adoptions_with_exposure','adoptions_neighbor_only']})
                vals['positive_potential_evaluations']=sum(z[c+'_positive_active'] for c in ['exposure','both','neighbor_change'])
                for band in ['below','equal','above']:
                    vals['evaluations_'+band]=sum(z[c+'_'+band] for c in ['exposure','both','neighbor_change'])
                process[(r['arm'],r['relative_cost'])].append(vals)
        assert len(block)==8000
        for k in range(400):
            for cost in [1.,1.2]:
                row=lookup[(pid,k,cost)]
                for mode in 'SPMZ':
                    assert float(row['G'+mode])==block[(k,'L'+mode,cost)]-block[(k,'D'+mode,None)]
                    assert float(row['local_global_'+mode])==block[(k,'L'+mode,cost)]-block[(k,'A'+mode,cost)]
        print('Verified raw',pid,flush=True)
    assert len(seen)==768000
    process_rows=[]
    for (arm,cost),values in sorted(process.items(),key=str):
        assert len(values)==38400
        z={'arm':arm,'relative_cost':cost,'trajectories':len(values)}
        z.update({n:float(np.mean([v[n] for v in values])) for n in values[0]})
        z['positive_potential_evaluation_fraction']=z['positive_potential_evaluations']/z['evaluation_events']
        process_rows.append(z)
    save(out/'process_descriptives.csv',process_rows)
    del process,rows,lookup
    rng=np.random.default_rng(2026100302);samples=10000
    boot=np.zeros((samples,2,len(names)))
    for i,pid in enumerate(ids):
        # Resample complete replicate blocks, preserving all conditions/costs.
        for start in range(0,samples,250):
            indices=rng.integers(0,400,size=(250,400))
            boot[start:start+250]+=data[i][indices].mean(axis=1)/96
        if (i+1)%12==0:print('Bootstrap profiles',i+1,'/96',flush=True)
    means=data.mean(axis=1).mean(axis=0);est=[];profile_est=[]
    for ri,cost in enumerate([1.,1.2]):
        for ni,name in enumerate(names):
            dist=boot[:,ri,ni];low,high=np.quantile(dist,[.025,.975])
            primary=name in PRIMARY
            alo,ahi=np.quantile(dist,[.05/8/2,1-.05/8/2]) if primary else (None,None)
            est.append({'relative_cost':cost,'contrast':name,'estimate':means[ri,ni],
                'ci95_low':low,'ci95_high':high,'ci99_375_low':alo,'ci99_375_high':ahi,
                'family':'primary' if primary else 'secondary_descriptive',
                'interpretation':classification(alo,ahi) if primary else 'descriptive'})
            for pi,pid in enumerate(ids):
                profile_est.append({'profile_id':pid,'relative_cost':cost,'contrast':name,
                                    'estimate':data[pi,:,ri,ni].mean()})
    save(out/'design_estimates.csv',est);save(out/'profile_estimates.csv',profile_est)
    with gzip.open(out/'bootstrap_design_means.csv.gz','wt',newline='') as f:
        w=csv.writer(f);w.writerow(['sample']+[str(r)+'_'+n for r in [1.,1.2] for n in names])
        w.writerows([k,*boot[k].flatten()] for k in range(samples))
    result={'status':'registered_main_analysis_complete','profiles':96,'replicates':400,
        'trajectories':768000,'bootstrap_samples':10000,'resampling_seed':2026100302,
        'primary_family_size':8,'diagnostic_margin':.5,'paired_block_resampling':True,
        'fixed_profiles_not_resampled':True,'raw_gaps_independently_reconciled':True,
        'source_manifest_sha256':sha(src/'manifest.json'),'source_contrasts_sha256':sha(src/'paired_contrasts.csv'),
        'output_sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
    (out/'analysis_manifest.json').write_text(json.dumps(result,indent=2))
    print(json.dumps([r for r in est if r['family']=='primary'],indent=2),flush=True)

if __name__=='__main__':main()
