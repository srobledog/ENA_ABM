import argparse
from ena_abm.mechanism_experiment import run

p=argparse.ArgumentParser()
p.add_argument('--config',default='configs/mechanisms_v0.1.json')
p.add_argument('--output',required=True)
p.add_argument('--workers',type=int,default=4)
p.add_argument('--stage',choices=['pilot','main'],default='pilot')
a=p.parse_args()
run(a.config,a.output,stage=a.stage,workers=a.workers)
