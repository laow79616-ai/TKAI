# Hyper Reasoning Confidence

Confidence records contain an optional confidence value, calibration metadata,
evidence coverage, reliability metadata, limitations, version history, and
evidence references. Confidence and evidence coverage are constrained to 0–1.

Confidence values describe metadata supplied by an owning framework. They are
not execution thresholds and never authorize actions. Consumers should display
limitations and calibration versions alongside values and should treat missing
values as unknown rather than zero.
