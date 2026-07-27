# Scoring

For alternative `a`, criterion `c`, weight `w`, score `s`, and confidence `q`:

`weighted_score(a) = q(a) × Σ(w(c) × s(a,c))`

Weights are normalized by contract and scores are bounded. Deterministic
ranking uses weighted score first, then lower risk, then higher net benefit.
The evaluation stores each weighted criterion contribution for sensitivity
analysis and reproducibility.
