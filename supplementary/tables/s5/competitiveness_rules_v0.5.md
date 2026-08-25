# Descriptive competitiveness rules v0.5

These shallow-tree rules summarize simulated profiles. They are not
causal claims or empirically estimated decision rules.

## Relative cost r=1.00

```text
|--- continuous__budget_limit <= -0.300
|   |--- continuous__beta_0 <= 1.317
|   |   |--- class: 1
|   |--- continuous__beta_0 >  1.317
|   |   |--- class: 1
|--- continuous__budget_limit >  -0.300
|   |--- continuous__market_sociality <= 0.433
|   |   |--- network__network_type_preferential_attachment <= 0.500
|   |   |   |--- class: 0
|   |   |--- network__network_type_preferential_attachment >  0.500
|   |   |   |--- class: 1
|   |--- continuous__market_sociality >  0.433
|   |   |--- continuous__status_mean <= 0.036
|   |   |   |--- class: 1
|   |   |--- continuous__status_mean >  0.036
|   |   |   |--- class: 1
```

## Relative cost r=1.20

```text
|--- continuous__market_sociality <= -0.217
|   |--- class: 0
|--- continuous__market_sociality >  -0.217
|   |--- continuous__beta_social <= -0.505
|   |   |--- class: 0
|   |--- continuous__beta_social >  -0.505
|   |   |--- continuous__uncertainty_mean <= -0.938
|   |   |   |--- class: 0
|   |   |--- continuous__uncertainty_mean >  -0.938
|   |   |   |--- class: 1
```

