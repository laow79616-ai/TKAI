from enum import Enum


class SimulationEvent(str, Enum):
    PROFILE_REGISTERED = "profile-registered"
    INPUT_VALIDATED = "input-validated"
    BASELINE_REGISTERED = "baseline-registered"
    MODEL_REGISTERED = "model-registered"
    SCENARIO_REGISTERED = "scenario-registered"
    SIMULATION_COMPLETED = "simulation-completed"
    FORECAST_GENERATED = "forecast-generated"
    FORECAST_EVALUATED = "forecast-evaluated"
    VALIDATION_FAILED = "validation-failed"
    RECOMMENDATION_GENERATED = "recommendation-generated"
    REVIEW_COMPLETED = "review-completed"
    LIFECYCLE_CHANGED = "lifecycle-changed"
    GOVERNANCE_ISSUE_DETECTED = "governance-issue-detected"
    COMPATIBILITY_ISSUE_DETECTED = "compatibility-issue-detected"
