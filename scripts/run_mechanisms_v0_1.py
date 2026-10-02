import argparse
from ena_abm.mechanism_experiment import run

p=argparse.ArgumentParser()
p.add_argument('--config',default='configs/mechanisms_v0.1.json')
p.add_argument('--output',required=True)
p.add_argument('--workers',type=int,default=4)
p.add_argument('--stage',choices=['pilot','main'],default='pilot')
p.add_argument('--resume',action='store_true')
p.add_argument('--minimum-free-gib',type=float,default=20)
p.add_argument('--stop-free-gib',type=float,default=5)
a=p.parse_args()
run(a.config,a.output,stage=a.stage,workers=a.workers,resume=a.resume,
    minimum_free_gib=a.minimum_free_gib,stop_free_gib=a.stop_free_gib)
