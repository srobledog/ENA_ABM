import math
import unittest
from dataclasses import asdict

from ena_abm.agents import ConsumerState
from ena_abm.config import ModelConfig
from ena_abm.decision import ParsimoniousDecisionRule
from ena_abm.mechanisms import MechanismModel
from ena_abm.mechanism_experiment import audit, configuration, profiles, selected_pilot_profiles, simple_benchmark
from ena_abm.model import EntrepreneurialNetworkActivationModel


class MechanismControlsTests(unittest.TestCase):
    def config(self, **updates):
        base=dict(n_consumers=10,mean_degree=4,seed_adopters=2,horizon=10,
            fairness_criterion='equal_budget',budget_limit=20.0,strategy='referral',
            direct_exposure_probability=.512,referral_acceptance_probability=.8,
            referral_neighbor_availability_probability=.8,referral_introduction_probability=.8)
        return ModelConfig.from_dict({**base,**updates})

    def test_full_matches_frozen_model_states_events_and_ticks(self):
        for strategy in ['direct','referral']:
            for accounting in ['upfront_expected','staged']:
                c=self.config(strategy=strategy,cost_accounting=accounting)
                base=EntrepreneurialNetworkActivationModel(c);expected=base.run()
                model=MechanismModel(c);actual=model.run()
                self.assertEqual(expected.summary,actual.summary)
                self.assertEqual(expected.ticks,actual.ticks)
                self.assertEqual([asdict(x) for x in base.consumers],[asdict(x) for x in model.consumers])
                self.assertEqual(len(expected.events),len(actual.events))
                for x,y in zip(expected.events,actual.events):self.assertEqual(x,{key:y[key] for key in x})

    def test_all_variants_share_initialization(self):
        c=self.config()
        signatures=set()
        for destination in ['L','A']:
            for b in [0,1]:
                for schedule in ['N','E']:
                    m=MechanismModel(c,destination_mode=destination,beta_social_mode=b,reevaluation_mode=schedule)
                    signatures.add(m.initialization_signature)
                    self.assertEqual(c.beta_individual,m.config.beta_individual)
                    self.assertEqual(c.market_sociality,m.config.market_sociality)
        self.assertEqual(len(signatures),1)

    def test_beta_off_removes_only_social_term(self):
        c=self.config(market_sociality=.8)
        model=MechanismModel(c,beta_social_mode=0)
        consumer=next(x for x in model.consumers if not x.adopted)
        a=model.decision_rule.evaluate(consumer,0)
        b=model.decision_rule.evaluate(consumer,1)
        self.assertEqual(a.utility,b.utility)
        self.assertEqual(a.probability,b.probability)
        self.assertNotEqual(a.social_evidence,b.social_evidence)
        self.assertEqual(a.utility,c.beta_0+c.beta_individual*(1-.8*consumer.uncertainty)*(consumer.fit-consumer.status_quo_satisfaction))
        self.assertGreater(a.social_reliance,0)

    def test_neutral_evidence_switch_has_identical_trajectories(self):
        for updates in [{'market_sociality':0.0},{'beta_social':0.0}]:
            for destination in ['L','A']:
                for schedule in ['N','E']:
                    c=self.config(**updates)
                    a=MechanismModel(c,destination_mode=destination,beta_social_mode=1,reevaluation_mode=schedule).run()
                    b=MechanismModel(c,destination_mode=destination,beta_social_mode=0,reevaluation_mode=schedule).run()
                    self.assertEqual(a.summary,b.summary);self.assertEqual(a.events,b.events)

    def test_no_referrers_never_start_or_draw_global_destination(self):
        m=MechanismModel(self.config(seed_adopters=0),destination_mode='A')
        before=m.destination_rng.getstate();out=m.run()
        self.assertEqual(before,m.destination_rng.getstate())
        self.assertEqual(out.summary['attempts_started'],0)
        self.assertEqual(out.summary['cost_spent'],0)
        audit(m,out)

    def test_failed_gates_do_not_draw_destination(self):
        for updates in [{'referral_acceptance_probability':0.0},
                {'referral_neighbor_availability_probability':0.0},{'referral_introduction_probability':0.0}]:
            c=self.config(**updates)
            a=MechanismModel(c,destination_mode='A');before=a.destination_rng.getstate();oa=a.run()
            b=MechanismModel(c);ob=b.run()
            self.assertEqual(before,a.destination_rng.getstate())
            self.assertEqual(oa.summary,ob.summary)
            self.assertEqual(oa.summary['exposures_delivered'],0)
            self.assertGreater(oa.summary['cost_spent'],0)

    def test_neighbor_change_generates_evaluation_only_in_N(self):
        c=self.config(strategy='direct',direct_exposure_probability=0.0,horizon=1,beta_0=100.0)
        initial=EntrepreneurialNetworkActivationModel(c)
        target=next(x for x in initial.consumers if not x.adopted and any(n in initial.seed_ids for n in initial.graph.neighbors(x.consumer_id)))
        target.state=ConsumerState.AWARE;target.awareness_time=0;target.last_evaluation_time=0;target.previous_adopted_neighbor_count=0
        n=MechanismModel(c,graph=initial.graph,consumers=initial.consumers,reevaluation_mode='N');on=n.run()
        e=MechanismModel(c,graph=initial.graph,consumers=initial.consumers,reevaluation_mode='E');oe=e.run()
        self.assertEqual(on.summary['new_adoptions'],1)
        self.assertEqual(oe.summary['new_adoptions'],0)
        self.assertEqual(next(x for x in on.events if x['event_type']=='evaluation')['evaluation_cause'],'neighbor_change')

    def test_exposure_only_still_receives_social_evidence(self):
        c=self.config(horizon=1,referral_acceptance_probability=1.0,
            referral_neighbor_availability_probability=1.0,referral_introduction_probability=1.0)
        model=MechanismModel(c,reevaluation_mode='E');out=model.run()
        evaluations=[x for x in out.events if x['event_type']=='evaluation']
        self.assertTrue(evaluations)
        self.assertTrue(any(x['social_utility_component']!=0 for x in evaluations))
        self.assertTrue(all(x['evaluation_cause']=='exposure' for x in evaluations))
        audit(model,out)

    def test_global_control_full_audit(self):
        for accounting in ['upfront_expected','staged']:
            for b in [0,1]:
                for schedule in ['N','E']:
                    m=MechanismModel(self.config(cost_accounting=accounting,horizon=30),destination_mode='A',beta_social_mode=b,reevaluation_mode=schedule)
                    out=m.run();a=audit(m,out)
                    self.assertEqual(a['adoptions_with_exposure']+a['adoptions_neighbor_only'],out.summary['new_adoptions'])

    def test_repeated_direct_exposures_are_retained(self):
        c=self.config(strategy='direct',direct_exposure_probability=1.0,beta_0=-100.,budget_limit=60.,horizon=30)
        m=MechanismModel(c);o=m.run();a=audit(m,o)
        self.assertGreater(a['repeat_exposures'],0)
        self.assertEqual(o.summary['new_adoptions'],0)

    def test_uniform_destination_uses_its_own_expected_draw(self):
        c=self.config(horizon=1,referral_acceptance_probability=1.,referral_neighbor_availability_probability=1.,referral_introduction_probability=1.)
        m=MechanismModel(c,destination_mode='A')
        import random
        expected_rng=random.Random();expected_rng.setstate(m.destination_rng.getstate())
        eligible=[x.consumer_id for x in m.consumers if not x.adopted]
        first=expected_rng.choice(eligible);eligible.remove(first);second=expected_rng.choice(eligible)
        o=m.run();events=[e for e in o.events if e['event_type']=='exposure']
        self.assertEqual([e['target_id'] for e in events],[first,second])

    def test_staged_coordination_failure_has_no_global_draw(self):
        m=MechanismModel(self.config(budget_limit=.6,cost_accounting='staged',referral_acceptance_probability=1.),destination_mode='A')
        before=m.destination_rng.getstate();o=m.run()
        self.assertEqual(before,m.destination_rng.getstate())
        self.assertEqual(o.summary['exposures_delivered'],0)
        self.assertLessEqual(o.summary['cost_spent'],.6)
        audit(m,o)

    def test_benchmark_has_parity_and_hand_computed_saturation(self):
        c=self.config(budget_limit=4,beta_0=0)
        model=EntrepreneurialNetworkActivationModel(c)
        for consumer in model.consumers:consumer.fit=consumer.status_quo_satisfaction=.5
        value=simple_benchmark(c,model.consumers,1.)
        self.assertAlmostEqual(value,8*(1-(1-.512*.5/8)**4),places=12)
        self.assertLessEqual(simple_benchmark(c,model.consumers,1.2),value)
        self.assertEqual(simple_benchmark(c.with_updates(budget_limit=0),model.consumers,1),0)

    def test_pilot_selection_uses_input_only(self):
        import json
        from ena_abm.mechanism_experiment import ROOT
        expected=json.loads((ROOT/'configs/mechanisms_v0.1.json').read_text())['pilot_profiles']
        self.assertEqual(selected_pilot_profiles(profiles()),expected)

    def test_invalid_switches_fail(self):
        for kw in [{'destination_mode':'bad'},{'beta_social_mode':2},{'reevaluation_mode':'bad'}]:
            with self.assertRaises(ValueError):MechanismModel(self.config(),**kw)

    def test_executor_complete_block_and_paired_contrasts(self):
        import tempfile,json,gzip,csv
        from pathlib import Path
        from ena_abm.mechanism_experiment import ROOT,worker
        spec=json.loads((ROOT/'configs/mechanisms_v0.1.json').read_text())
        profile=next(p for p in profiles() if p['profile']=='P008')
        with tempfile.TemporaryDirectory() as directory:
            result=worker((profile,spec,'pilot',directory,1))
            self.assertEqual(result['files']['runs']['rows'],20)
            self.assertEqual(result['files']['ticks']['rows'],600)
            self.assertEqual(result['files']['initializations']['rows'],1)
            with gzip.open(Path(directory)/'P008/runs.jsonl.gz','rt') as f:runs=[json.loads(v) for v in f]
            self.assertEqual(len({r['initialization_signature'] for r in runs}),1)
            for row in result['contrasts']:
                schedule=row['schedule'];cost=row['r']
                outputs={r['arm']:r['summary']['new_adoptions'] for r in runs if r['relative_cost'] in {None,cost}}
                full=outputs['L1'+schedule]-outputs['D1'+schedule]
                random=outputs['A1'+schedule]-outputs['D1'+schedule]
                off=outputs['L0'+schedule]-outputs['D0'+schedule]
                random_off=outputs['A0'+schedule]-outputs['D0'+schedule]
                self.assertEqual(row['G'],full)
                self.assertEqual(row['L'],full-random)
                self.assertEqual(row['B'],full-off)
                self.assertEqual(row['I'],full-random-off+random_off)


    def test_trace_is_published_only_after_complete_close(self):
        import tempfile,gzip,hashlib
        from pathlib import Path
        from ena_abm.mechanism_experiment import DeterministicWriter
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'trace.jsonl.gz'
            writer=DeterministicWriter(path);writer.write({'state':'complete'})
            self.assertFalse(path.exists())
            metadata=writer.close()
            self.assertTrue(path.exists())
            self.assertFalse(writer.temporary.exists())
            with gzip.open(path,'rb') as f:data=f.read()
            self.assertEqual(hashlib.sha256(data).hexdigest(),metadata['content_sha256'])


if __name__=='__main__':unittest.main()
