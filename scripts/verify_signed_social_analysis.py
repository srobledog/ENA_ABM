"""Independent uncertainty check using the exact empirical-bootstrap variance."""
import csv,gzip,json
from pathlib import Path
import argparse
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('analysis');a=p.parse_args()
    src=Path(a.source);out=Path(a.analysis)
    with (src/'paired_contrasts.csv').open() as f:rows=list(csv.DictReader(f))
    with (out/'design_estimates.csv').open() as f:est=list(csv.DictReader(f))
    with gzip.open(out/'bootstrap_design_means.csv.gz','rt') as f:boot=list(csv.DictReader(f))
    primary=[r for r in est if r['family']=='primary'];assert len(primary)==8 and len(boot)==10000
    ids=sorted({r['profile_id'] for r in rows});checks=[]
    for e in primary:
        cost=float(e['relative_cost']);name=e['contrast']
        matrix=np.array([[float(r[name]) for r in rows if r['profile_id']==pid and float(r['r'])==cost] for pid in ids])
        assert matrix.shape==(96,400)
        mean=matrix.mean();exact_var=matrix.var(axis=1,ddof=0).sum()/400/96**2
        draws=np.array([float(r[str(cost)+'_'+name]) for r in boot])
        ratio=draws.var(ddof=1)/exact_var
        bias_z=abs(draws.mean()-mean)/(exact_var/len(draws))**.5
        assert abs(mean-float(e['estimate']))<1e-12
        assert .90<ratio<1.10,(name,ratio)
        assert bias_z<5,(name,bias_z)
        q=np.quantile(draws,[.05/8/2,1-.05/8/2])
        np.testing.assert_allclose(q,[float(e['ci99_375_low']),float(e['ci99_375_high'])],atol=1e-12,rtol=0)
        checks.append({'relative_cost':cost,'contrast':name,'variance_ratio_bootstrap_to_exact':ratio,
                       'bootstrap_mean_monte_carlo_z':bias_z})
    result={'status':'passed','checks':checks,'exact_variance_formula':'sum(profile population variances) / 400 / 96^2',
            'scope':'Mean, empirical-bootstrap variance and Bonferroni interval verification for all eight primary contrasts'}
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
