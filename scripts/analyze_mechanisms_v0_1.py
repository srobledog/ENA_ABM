import argparse

from ena_abm.mechanism_analysis import analyze

p = argparse.ArgumentParser()
p.add_argument("--input", required=True)
p.add_argument("--output", required=True)
p.add_argument("--config", default="configs/mechanisms_v0.1.json")
p.add_argument("--allow-technical-pilot", action="store_true")
p.add_argument("--bootstrap-samples", type=int)
a = p.parse_args()
analyze(a.input, a.output, a.config, allow_technical_pilot=a.allow_technical_pilot,
        bootstrap_samples=a.bootstrap_samples)
