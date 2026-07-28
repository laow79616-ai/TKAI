# Perception

Perception records input-source references, normalization strategy, extracted
features, fused context, and a calibrated confidence in `[0, 1]`. Raw secrets
or credentials must never be used as sources; callers store managed
references instead.
