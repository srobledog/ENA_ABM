import unittest
from dataclasses import asdict
from ena_abm.signed_social import SignedModel, signed_audit
from ena_abm.mechanisms import MechanismModel
from ena_abm.mechanism_experiment import configuration, profiles
from ena_abm.rng import stable_seed


class SignedTests(unittest.TestCase):
    def test_pointwise_identities(self):
        p=profiles()[0]
        for beta in [0.,2.]:
            c=configuration(p,replicate=0,master_seed=123,strategy='direct').with_updates(beta_social=beta)
            models={m:SignedModel(c,social_mode=m) for m in 'SPMZ'}
            person=models['S'].consumers[0]
            for s in [0.,.25,.5,.75,1.]:
                e={m:x.decision_rule.evaluate(person,s) for m,x in models.items()}
                self.assertAlmostEqual(e['S'].utility-e['Z'].utility,
                                       e['P'].utility+e['M'].utility-2*e['Z'].utility)
                self.assertGreaterEqual(e['P'].utility,e['Z'].utility)
                self.assertLessEqual(e['M'].utility,e['Z'].utility)
                for v in e.values():self.assertTrue(0<=v.probability<=1)
                if s<=.5:self.assertEqual(e['P'].utility,e['Z'].utility)
                if s>=.5:self.assertEqual(e['M'].utility,e['Z'].utility)

    def test_sixty_legacy_trajectories(self):
        for p in [x for x in profiles() if x['profile'] in ['P069','P062']]:
            for k in range(3):
                seed=stable_seed(2026100201,'mechanisms_v0.1_pilot',p['profile'],k)
                for m,b in [('S',1),('Z',0)]:
                    for strategy,dest,r in [('direct','L',1.)]+[('referral',d,r) for d in ['L','A'] for r in [1.,1.2]]:
                        c=configuration(p,replicate=k,master_seed=seed,strategy=strategy,cost=r)
                        old=MechanismModel(c,destination_mode=dest,beta_social_mode=b)
                        new=SignedModel(c,destination_mode=dest,social_mode=m)
                        a=old.run();z=new.run();signed_audit(new,z)
                        self.assertEqual(a.summary,z.summary);self.assertEqual(a.ticks,z.ticks)
                        self.assertEqual([asdict(x) for x in old.consumers],[asdict(x) for x in new.consumers])
                        self.assertEqual(len(a.events),len(z.events))
                        for x,y in zip(a.events,z.events):self.assertEqual(x,{k:y[k] for k in x})

    def test_new_variants_audited(self):
        for mode in ['P','M']:
            for dest in ['L','A']:
                c=configuration(profiles()[0],replicate=0,master_seed=127,strategy='referral')
                model=SignedModel(c,social_mode=mode,destination_mode=dest)
                signed_audit(model,model.run())
