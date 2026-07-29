# Operations Guide

Use the dashboard for Learning Overview, Patterns, Lessons, Recommendations,
Analytics, and History. Use the GET-only endpoints under `/tiktok/learning`.
Expose the Prometheus text endpoint at `/tiktok/learning/metrics`.

Grant only `tiktok:learning:read` to dashboard and API readers. Offline jobs may
receive `manage`, `analyze`, or `recommend` permissions as narrowly required.
Audit profile, pattern, lesson, and recommendation events. Do not put secrets in
profile metadata or logs. Investigate empty results by checking the profile's
module list, subject, evidence availability, and minimum sample threshold.
