"""Prospective signed-social robustness extension; original model untouched."""
import math
from dataclasses import replace
from .decision import ParsimoniousDecisionRule
from .mechanisms import MechanismModel
from .mechanism_experiment import audit


class SignedRule(ParsimoniousDecisionRule):
    def __init__(self, config, mode):
        super().__init__(config)
        if mode not in {'S','P','M','Z'}: raise ValueError(mode)
        self.mode = mode

    def evaluate(self, consumer, social_evidence):
        e = super().evaluate(consumer, social_evidence)
        if self.mode in {'S','Z'}: return e
        signed = self.config.beta_social * e.social_reliance * (2*e.social_evidence-1)
        component = max(signed,0.) if self.mode=='P' else min(signed,0.)
        u = (self.config.beta_0 + self.config.beta_individual *
             (1-e.social_reliance)*e.individual_evaluation + component)
        return replace(e,utility=u,probability=self._logistic(u))


class SignedModel(MechanismModel):
    def __init__(self, config, *, social_mode, destination_mode='L'):
        if social_mode not in {'S','P','M','Z'}: raise ValueError(social_mode)
        if config.beta_social < 0: raise ValueError('Requires nonnegative coefficient')
        self.social_mode = social_mode
        self.original_beta_social = config.beta_social
        super().__init__(config,destination_mode=destination_mode,
                         beta_social_mode=int(social_mode!='Z'),reevaluation_mode='N')
        self.decision_rule = SignedRule(self.config,social_mode)

    def _record_evaluation(self, pending, adopted):
        super()._record_evaluation(pending,adopted)
        row=self.event_records[-1]
        w=self.original_beta_social*pending.social_reliance
        signed=w*(2*pending.social_evidence-1)
        positive=max(signed,0.); negative=min(signed,0.)
        row.update(social_weight=w,positive_component=positive,negative_component=negative,
                   individual_base=self.config.beta_0+row['individual_utility_component'],
                   previous_exposures=self._exposure_counts[pending.consumer_id],
                   social_mode=self.social_mode)
        row['social_utility_component']={'S':signed,'P':positive,'M':negative,'Z':0.}[self.social_mode]


def signed_audit(model, output):
    result=audit(model,output)
    bins={f'{cause}_{band}':0 for cause in ['exposure','both','neighbor_change']
          for band in ['below','equal','above','positive_active']}
    adopted=set(model.seed_ids); pending=set();tick=None
    for e in output.events:
        if e['tick']!=tick:
            adopted.update(pending);pending=set();tick=e['tick']
        if e['event_type']!='evaluation': continue
        neighbors=model.graph.neighbors(e['target_id'])
        s=sum(n in adopted for n in neighbors)/len(neighbors) if neighbors else 0.
        assert s==e['social_evidence']
        w=model.original_beta_social*e['social_reliance'];z=w*(2*s-1)
        pos=max(z,0.);neg=min(z,0.)
        assert math.isclose(pos+neg,z,abs_tol=1e-12)
        expected={'S':z,'P':pos,'M':neg,'Z':0.}[model.social_mode]
        assert e['positive_component']==pos and e['negative_component']==neg
        assert e['social_utility_component']==expected
        assert math.isclose(e['utility'],e['individual_base']+expected,abs_tol=1e-12)
        assert math.isclose(e['probability'],ParsimoniousDecisionRule._logistic(e['utility']),abs_tol=1e-12)
        band='below' if s<.5 else 'above' if s>.5 else 'equal'
        bins[e['evaluation_cause']+'_'+band]+=1
        bins[e['evaluation_cause']+'_positive_active']+=int(pos>0)
        if e['adopted']:pending.add(e['target_id'])
    result.update(bins)
    return result
