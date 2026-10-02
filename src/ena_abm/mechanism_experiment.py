"""Paired mechanism experiment with complete, deterministic event traces."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import platform
import statistics
import subprocess
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .config import ModelConfig
from .mechanisms import MechanismModel
from .model import EntrepreneurialNetworkActivationModel
from .rng import stable_seed

ROOT = Path(__file__).resolve().parents[2]


def configuration(profile, *, replicate, master_seed, strategy, cost=1.0, accounting="upfront_expected"):
    """Reuse the archived study mapping, including beta concentration 10."""
    original = json.loads((ROOT/'configs/main_study_v0.5.json').read_text())
    values = dict(original['main_design']['fixed_parameters'])
    values.update({k: float(v) for k, v in profile.items() if k not in {'profile', 'network_type'}})
    values['network_type'] = profile['network_type']
    for name, stem in [('status_mean','status'), ('uncertainty_mean','uncertainty')]:
        mean = values.pop(name)
        values[stem+'_alpha'] = 10.0 * mean
        values[stem+'_beta'] = 10.0 * (1.0 - mean)
    values['seed_adopters'] = int(values['seed_adopters'])
    values.update(fairness_criterion='equal_budget', action_budget=999, exposure_quota=999,
        strategy=strategy, direct_action_cost=1.0, referral_action_cost=cost,
        cost_accounting=accounting, replicate_id=replicate, master_seed=master_seed,
        allow_repeated_direct_contact=True)
    return ModelConfig.from_dict(values)


def profiles():
    with (ROOT/'results/summaries/registered_profiles_v0.5.csv').open() as f:
        return list(csv.DictReader(f))


def selected_pilot_profiles(all_profiles):
    selected = []
    for network in ['ring','small_world','preferential_attachment']:
        remaining = [r for r in all_profiles if r['network_type'] == network]
        for social,budget in [(0,0),(0,1),(1,0),(1,1)]:
            r = min(remaining, key=lambda r: ((float(r['market_sociality'])-social)**2
                + ((float(r['budget_limit'])-8)/52-budget)**2, r['profile']))
            remaining.remove(r)
            selected.append(r['profile'])
    return selected


def simple_benchmark(config, consumers, cost):
    nonseed = [c for c in consumers if not c.is_seed]
    m = min(math.floor(config.budget_limit/cost), config.actions_per_tick*config.horizon)
    expected = 0.0
    for c in nonseed:
        u = max(config.minimum_uncertainty, .85*c.initial_uncertainty)
        rho = config.market_sociality*u
        utility = config.beta_0 + config.beta_individual*(1-rho)*(c.fit-c.status_quo_satisfaction)
        q = 1/(1+math.exp(-utility))
        expected += -math.expm1(m*math.log1p(-.512*q/len(nonseed)))
    return expected


def audit(model, output):
    """Validate scientific invariants on every trajectory, not only examples."""
    adopted = set(model.seed_ids)
    aware = set(model.seed_ids)
    exposed_counts = Counter()
    evaluations = Counter()
    causes = Counter()
    adoptions_by_cause = Counter()
    exposure_degrees = []
    exposure_shares = []
    by_tick = {}
    for e in output.events:
        by_tick.setdefault(e['tick'], []).append(e)
    assert len(output.ticks) == model.config.horizon
    for tick in range(1, model.config.horizon+1):
        events = by_tick.get(tick, [])
        targets = set()
        pending = set()
        tick_exposed = set()
        for e in events:
            if e['event_type'] == 'exposure':
                target = e['target_id']
                assert target not in adopted and target not in targets
                assert e['target_previous_exposures'] == exposed_counts[target]
                assert (e['target_state_before'] != 'unaware') == (target in aware)
                assert e['target_degree'] == model.graph.degree(target)
                neighbors = model.graph.neighbors(target)
                share = sum(n in adopted for n in neighbors)/len(neighbors) if neighbors else 0.0
                assert e['target_neighbor_adopted_share'] == share
                if e['exposure_kind'] == 'referral':
                    assert e['source_id'] in adopted
                    candidate = e['local_candidate_id']
                    assert candidate in model.graph.neighbors(e['source_id']) and candidate not in adopted
                    assert candidate not in targets
                    if model.destination_mode == 'L': assert candidate == target
                targets.add(target); tick_exposed.add(target); aware.add(target)
                exposed_counts[target] += 1
                exposure_degrees.append(e['target_degree']); exposure_shares.append(share)
            elif e['event_type'] == 'evaluation':
                target = e['target_id']
                assert target in aware and target not in adopted and target not in pending
                assert e['first_evaluation'] == (evaluations[target] == 0)
                cause = e['evaluation_cause']
                assert (cause in {'exposure','both'}) == (target in tick_exposed)
                if model.reevaluation_mode == 'E': assert cause == 'exposure'
                if model.beta_social_mode == 0: assert e['social_utility_component'] == 0.0
                assert math.isclose(e['utility'], model.config.beta_0+e['individual_utility_component']+e['social_utility_component'], abs_tol=1e-12)
                evaluations[target] += 1; causes[cause] += 1
                if e['adopted']:
                    pending.add(target); adoptions_by_cause[cause] += 1
        adopted.update(pending)
        row = output.ticks[tick-1]
        assert row['new_adoptions_this_tick'] == len(pending)
        assert row['total_adopters'] == len(adopted)
        assert row['cost_spent'] <= model.config.budget_limit + 1e-9
    costs = sum(e['cost_increment'] for e in output.events if e['event_type']=='cost')
    assert math.isclose(costs, output.summary['cost_spent'],abs_tol=1e-9)
    assert len(adopted-model.seed_ids) == output.summary['new_adoptions']
    assert sum(exposed_counts.values()) == output.summary['exposures_delivered']
    assert sum(evaluations.values()) == output.summary['evaluation_events']
    return dict(unique_exposed=len(exposed_counts), repeat_exposures=sum(exposed_counts.values())-len(exposed_counts),
        first_evaluations=len(evaluations), reevaluations=sum(evaluations.values())-len(evaluations),
        evaluations_exposure=causes['exposure'],evaluations_neighbor_change=causes['neighbor_change'],evaluations_both=causes['both'],
        adoptions_with_exposure=adoptions_by_cause['exposure']+adoptions_by_cause['both'],
        adoptions_neighbor_only=adoptions_by_cause['neighbor_change'],
        mean_exposure_degree=statistics.fmean(exposure_degrees) if exposure_degrees else None,
        mean_exposure_neighbor_share=statistics.fmean(exposure_shares) if exposure_shares else None,
        exposure_denominator_missing=not exposed_counts,
        final_state_sha256=hashlib.sha256(canonical([asdict(c) for c in model.consumers]).encode()).hexdigest())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=False, allow_nan=False)


class DeterministicWriter:
    def __init__(self,path):
        self.path = Path(path)
        self.temporary = self.path.with_name(self.path.name+'.part')
        self.raw = self.temporary.open('wb')
        self.gz = gzip.GzipFile(filename='',fileobj=self.raw, mode='wb', compresslevel=3,mtime=0)
        self.handle = io.TextIOWrapper(self.gz,encoding='utf-8',newline='')
        self.digest = hashlib.sha256(); self.rows = 0; self.bytes = 0
    def write(self, value):
        line = canonical(value)+'\n'
        self.handle.write(line); data=line.encode();self.digest.update(data);self.rows+=1;self.bytes+=len(data)
    def close(self):
        self.handle.close()
        self.raw.flush();os.fsync(self.raw.fileno());self.raw.close()
        os.replace(self.temporary,self.path)
        return {'rows':self.rows,'uncompressed_bytes':self.bytes,'content_sha256':self.digest.hexdigest()}


def worker(payload):
    profile, specification, stage, output_dir, replicates = payload
    begin = time.perf_counter()
    root=Path(output_dir)/profile['profile'];root.mkdir(parents=True,exist_ok=False)
    writers={key:DeterministicWriter(root/(key+'.jsonl.gz')) for key in ['runs','ticks','events','initializations','final_states','benchmarks']}
    cells = []
    for k in range(replicates):
        namespace = specification['pilot_namespace'] if stage=='pilot' else specification['main_namespace']
        seed=stable_seed(specification['experiment_seed'],namespace,profile['profile'],k)
        common_config=configuration(profile,replicate=k,master_seed=seed,strategy='direct')
        initial=EntrepreneurialNetworkActivationModel(common_config)
        block={'protocol_version':'0.1','base_commit':specification['base_commit'],'profile_id':profile['profile'],
               'stage':stage,'replicate_id':k,'master_seed':seed,'initialization_signature':initial.initialization_signature}
        writers['initializations'].write({**block,'configuration':common_config.to_dict(),
            'edges':initial.graph.edges(),'consumers':[asdict(c) for c in initial.consumers]})
        direct_benchmark=simple_benchmark(common_config,initial.consumers,1.0)
        for r in specification['relative_costs']:
            writers['benchmarks'].write({**block,'relative_cost':r,'direct_simple':direct_benchmark,
                'referral_simple':simple_benchmark(common_config,initial.consumers,r),
                'delta_simple':simple_benchmark(common_config,initial.consumers,r)-direct_benchmark})
        direct = {}
        gaps = {}
        for social in specification['evidence_modes']:
            for schedule in specification['reevaluation_modes']:
                config=common_config
                m=MechanismModel(config,beta_social_mode=social,reevaluation_mode=schedule)
                o=m.run(); validation=audit(m,o)
                assert o.initialization_signature==initial.initialization_signature
                direct[(social,schedule)]=o.summary['new_adoptions']
                emit(writers,block,m,o,validation,f'D{social}{schedule}',None)
                for destination in specification['destinations']:
                    for r in specification['relative_costs']:
                        config=configuration(profile,replicate=k,master_seed=seed,strategy='referral',cost=r)
                        m=MechanismModel(config,destination_mode=destination,beta_social_mode=social,reevaluation_mode=schedule)
                        o=m.run();validation=audit(m,o)
                        assert o.initialization_signature==initial.initialization_signature
                        emit(writers,block,m,o,validation,f'{destination}{social}{schedule}',r)
                        gaps[(destination,social,schedule,r)] = o.summary['new_adoptions']-direct[(social,schedule)]
        for r in specification['relative_costs']:
            for schedule in specification['reevaluation_modes']:
                g=lambda d,b:gaps[(d,b,schedule,r)]
                cells.append({'profile_id':profile['profile'],'replicate_id':k,'r':r,'schedule':schedule,
                    'G':g('L',1),'G_A1':g('A',1),'G_L0':g('L',0),'G_A0':g('A',0),
                    'L':g('L',1)-g('A',1),'B':g('L',1)-g('L',0),
                    'I':g('L',1)-g('A',1)-g('L',0)+g('A',0)})
    files = {key: writer.close() for key,writer in writers.items()}
    for key in files:
        p=root/(key+'.jsonl.gz');files[key].update(compressed_bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    write_csv(root/'paired_contrasts.csv',cells)
    return {'profile_id':profile['profile'],'network_type':profile['network_type'],'replicates':replicates,
        'elapsed_seconds':time.perf_counter()-begin,'files':files,'contrasts':cells}


def emit(writers,block,m,o,validation,arm,cost):
    meta={**block,'arm':arm,'strategy':m.config.strategy,'destination_mode':m.destination_mode if m.config.strategy=='referral' else None,
          'beta_social_mode':m.beta_social_mode,'reevaluation_mode':m.reevaluation_mode,
          'relative_cost':cost,'cost_accounting':m.config.cost_accounting}
    writers['runs'].write({**meta,'summary':o.summary,'audit':validation})
    for row in o.events:writers['events'].write({**meta,**row})
    for row in o.ticks:writers['ticks'].write({**meta,**row})
    writers['final_states'].write({**meta,'consumers':[asdict(c) for c in m.consumers]})


def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def run(specification_path,output_dir,stage='pilot',workers=4):
    specification=json.loads(Path(specification_path).read_text())
    if stage == 'main' and not specification.get('main_execution_authorized_by_this_pilot', False):
        raise ValueError('This frozen configuration authorizes the technical pilot only')
    all_profiles=profiles()
    assert selected_pilot_profiles(all_profiles)==specification['pilot_profiles']
    selected=[next(p for p in all_profiles if p['profile']==pid) for pid in specification['pilot_profiles']] if stage=='pilot' else all_profiles
    replicates=specification['pilot_replicates'] if stage=='pilot' else specification['main_replicates']
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'profiles.csv',selected)
    begin=time.perf_counter()
    payloads=[(p,specification,stage,str(output),replicates) for p in selected]
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(worker,payloads):
            results.append(result)
            print(f"Completed {result['profile_id']}: {result['files']['runs']['rows']} trajectories",flush=True)
    contrasts=[r for profile in results for r in profile.pop('contrasts')]
    write_csv(output/'paired_contrasts.csv',contrasts)
    summaries=[]
    for pid in [p['profile'] for p in selected]:
        for r in specification['relative_costs']:
            for schedule in specification['reevaluation_modes']:
                rows=[v for v in contrasts if v['profile_id']==pid and v['r']==r and v['schedule']==schedule]
                for contrast in ['G','L','B','I']:
                    values=[v[contrast] for v in rows]
                    summaries.append({'profile_id':pid,'r':r,'schedule':schedule,'contrast':contrast,
                        'replicates':len(values),'mean':statistics.fmean(values),'mcse':statistics.stdev(values)/math.sqrt(len(values))})
    write_csv(output/'technical_precision.csv',summaries)
    manifest={'protocol_version':'0.1','base_commit':specification['base_commit'],
        'extension_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'status':'technical_pilot_only' if stage=='pilot' else 'main',
        'stage':stage,'specification':specification,'profiles':len(selected),'replicates':replicates,
        'unique_trajectories':sum(p['files']['runs']['rows'] for p in results),
        'paired_comparisons':len(selected)*replicates*16,
        'elapsed_seconds':time.perf_counter()-begin,'workers':workers,'python':platform.python_version(),
        'platform':platform.platform(),'per_profile':results,
        'full_data_sha256':{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob('*')) if p.is_file()}}
    for profile in results:
        for kind, metadata in profile['files'].items():
            name=profile['profile_id']+'/'+kind+'.jsonl.gz'
            assert manifest['full_data_sha256'][name]==metadata['sha256'], ('stored file changed',name)
            with gzip.open(output/name,'rb') as handle:
                logical=hashlib.sha256();length=0
                for chunk in iter(lambda:handle.read(1024*1024),b''):
                    logical.update(chunk);length+=len(chunk)
            assert logical.hexdigest()==metadata['content_sha256'] and length==metadata['uncompressed_bytes'], ('stored trace incomplete',name)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(f"Finished {manifest['unique_trajectories']} unique trajectories in {manifest['elapsed_seconds']:.1f} s",flush=True)
    return manifest
