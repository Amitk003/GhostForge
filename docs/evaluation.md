# Evaluation

How we test GhostForge and how you should read the numbers.

## Why honest testing matters

Many papers report 99 percent accuracy on CIC-IDS2018 with a simple split. That number is not real. The dataset has duplicate features, wrong flow directions, and attacker IPs that leak the label. A model that memorizes those clues looks good but fails on a new network.

We test in three ways:

1. In dataset: train on 80 percent of CIC, test on 20 percent. This is the easy test.
2. Cross dataset: train on CIC, test on CTU-13. This checks if the model learned real patterns or just CIC quirks.
3. Held out family: train without one attack family like Infiltration, test on it. This checks zero day ability.

We also never report only accuracy. We report lead time at 1 percent false positive rate. This means how many windows before the attack we warn, when we keep false alarms at 1 percent. A SOC cares about this, not just F1.

## Metrics

* Precision: of all alerts, how many were real attacks
* Recall: of all real attacks, how many we caught
* F1: balance of precision and recall
* FPR: false positive rate, lower is better, best teams keep under 10 percent, many teams are at 50 percent
* Lead Time: windows of early warning at 1 percent FPR, higher is better
* Alert reduction: how many alerts we removed at same recall

## Baselines

We compare on same features:

* Logistic Regression
* XGBoost with focal loss
* Vanilla LSTM on flat vectors

GhostForge should beat them on cross dataset and held out tests, not just in dataset.

## How to run

```bash
python scripts/evaluate.py --pred benchmarks/output.json --gt data/processed/labels.csv
make test
```

This prints a table like:

```
Model                F1    Precision  Recall  FPR   Lead Time
LogReg baseline      -     -          -       -     -
GhostForge Twin      -     -          -       -     -
```

Full results go to `benchmarks/` as json and plots.

## What we report openly

* Where we win and where we lose
* FPR at same recall, not just best F1
* Failure cases like slow scan that looks like normal
* Ablation: graph vs flat, single vs multi scale, with vs without validator, with vs without codebook

## Leak audit

Before each run we check:

```bash
grep -r "192.168" data/processed
```

This should be zero after we strip IPs. If not, we have leakage and the test is not honest.

## Reproduce

```bash
pip install -e ".[dev]"
pytest --cov=ghostforge
python scripts/train.py --config configs/base.yaml --data data/processed
python scripts/evaluate.py --pred benchmarks/output.json --gt data/processed/labels.csv
```

With seed 42 you should get the same codebook map. See `configs/base.yaml` for all settings.
