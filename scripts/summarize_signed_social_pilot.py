"""Descriptive technical-pilot summaries; no inferential efficacy tests."""
import argparse,csv,gzip,json,statistics,hashlib
from collections import defaultdict
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');a=parser.parse_args()
    src=Path(a.source);out=Path(a.output);out.mkdir(exist_ok=True,parents=True)
    manifest=json.loads((src/'manifest.json').read_text());assert manifest['trajectories']==24000
    groups=defaultdict(list);seen=set();rows=[]
    for p in manifest['per_profile']:
        path=src/p['profile_id']/'runs.jsonl.gz'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p['files']['runs']['sha256']
        with gzip.open(path,'rt') as f:
            for line in f:
                r=json.loads(line);key=(r['profile_id'],r['replicate_id'],r['arm'],r['relative_cost'])
                assert key not in seen;seen.add(key)
                groups[(r['arm'],r['relative_cost'])].append(r)
    assert len(seen)==24000 and len(groups)==20
    for (arm,cost),items in sorted(groups.items(),key=str):
        assert len(items)==1200
        row={'arm':arm,'relative_cost':cost,'trajectories':len(items)}
        for m in ['new_adoptions','exposures_delivered']:
            row[m]=statistics.fmean(r['summary'][m] for r in items)
        for m in ['unique_exposed','repeat_exposures']:
            row[m]=statistics.fmean(r['audit'][m] for r in items)
        total=sum(r['summary']['evaluation_events'] for r in items)
        row['evaluation_events']=total
        for band in ['below','equal','above','positive_active']:
            n=sum(r['audit'][c+'_'+band] for r in items for c in ['exposure','both','neighbor_change'])
            row['evaluation_'+band+'_fraction']=n/total if total else None
        rows.append(row)
    def save(name,items):
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    save('pilot_arm_descriptives.csv',rows)
    with (src/'paired_contrasts.csv').open() as f:paired=list(csv.DictReader(f))
    assert len(paired)==2400
    summaries=[]
    for r in [1.,1.2]:
        subset=[x for x in paired if float(x['r'])==r];assert len(subset)==1200
        for name in [k for k in subset[0] if k not in ['profile_id','replicate_id','r']]:
            summaries.append({'relative_cost':r,'contrast':name,'mean':statistics.fmean(float(x[name]) for x in subset),
                              'status':'technical_pilot_descriptive_only'})
    save('pilot_contrast_descriptives.csv',summaries)
    compressed=sum(v['compressed_bytes'] for p in manifest['per_profile'] for v in p['files'].values())
    worker_seconds=sum(p['elapsed_seconds'] for p in manifest['per_profile'])
    estimates={'pilot_trajectories':24000,'pilot_compressed_stream_bytes':compressed,
        'pilot_worker_seconds':worker_seconds,'main_projection_factor':32,
        'main_projected_compressed_stream_gib':compressed*32/2**30,
        'main_projected_hours_two_workers':worker_seconds*32/2/3600,
        'projection_limit':'Linear extrapolation from selected pilot profiles, not a resource guarantee; excludes packaging, verification and transfer overhead.'}
    (out/'technical_estimates.json').write_text(json.dumps(estimates,indent=2))
    print(json.dumps({'estimates':estimates,'contrasts':[x for x in summaries if x['contrast'] in ['GS','GP','GM','GZ','BP','BM','H','D_components']],
        'positive_active_fractions':{str((x['arm'],x['relative_cost'])):x['evaluation_positive_active_fraction'] for x in rows}},indent=2))

if __name__=='__main__':main()
