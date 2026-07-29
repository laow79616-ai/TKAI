# State Machine

Call `transition` with the state ID, next state, next lifecycle, and expected
version. The framework checks isolation, current version, and lifecycle legality
before creating a transition record and replacing the immutable state. A
compatibility transition must be registered and explicitly requested.
