"""Compare new baseline with the published release and untouched implementation."""
import argparse
import csv
import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from ena_abm.mechanism_experiment import ROOT,configuration,profiles,canonical
from ena_abm.mechanisms import MechanismModel
from ena_abm.model import EntrepreneurialNetworkActivationModel

p=argparse.ArgumentParser();p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
spec=json.loads((ROOT/'configs/mechanisms_v0.1.json').read_text())
selected=set(spec['pilot_profiles'])
lookup={v['profile']:v for v in profiles()}
report={'published_pairs_checked':0,'original_fields_checked':0,'state_and_event_trajectory_checks':0,
    'release_commit':spec['base_commit'],'archived_subsets':{},'mismatches':[]}
matched=[]
for filename,cost in [('main_paired_runs_v0.5.csv.gz',1.0),('main_fixed_cost_1.20_runs_v0.5.csv.gz',1.2)]:
    path=Path(a.archive_dir)/filename
    subset=[]
    with gzip.open(path,'rt') as f:
        for row in csv.DictReader(f):
            if row['scenario'] not in selected or int(row['replicate'])>=10 or float(row['r'])!=cost:continue
            seed=int(row['master_seed']);rep=int(row['replicate'])
            for strategy in ['direct','referral']:
                c=configuration(lookup[row['scenario']],replicate=rep,master_seed=seed,strategy=strategy,cost=cost if strategy=='referral' else 1.)
                model=MechanismModel(c);actual=model.run()
                original=EntrepreneurialNetworkActivationModel(c);expected=original.run()
                assert actual.summary==expected.summary
                assert actual.ticks==expected.ticks
                assert [asdict(v) for v in model.consumers]==[asdict(v) for v in original.consumers]
                assert len(actual.events)==len(expected.events)
                assert all({key:actual.events[i][key] for key in event}==event for i,event in enumerate(expected.events))
                report['state_and_event_trajectory_checks']+=1
                assert actual.initialization_signature==row['initialization_signature']
                for field,value in row.items():
                    prefix=strategy+'_'
                    if not field.startswith(prefix):continue
                    observed=actual.summary[field[len(prefix):]]
                    if value=='': assert observed==''
                    else: assert float(value)==float(observed),(row['scenario'],rep,cost,field,value,observed)
                    report['original_fields_checked']+=1
            subset.append(row);matched.append(row);report['published_pairs_checked']+=1
    assert len(subset)==120,(filename,len(subset))
    report['archived_subsets'][filename]={'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'matched_pairs':len(subset),'matched_rows_sha256':hashlib.sha256(canonical(subset).encode()).hexdigest()}
assert report['published_pairs_checked']==240
report['status']='passed'
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
(out/'verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
with (out/'frozen_reference_240_pairs.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(matched[0]));writer.writeheader();writer.writerows(matched)
print(json.dumps(report,indent=2))
