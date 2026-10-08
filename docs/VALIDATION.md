# Validation record

Date: 2026-10-07
Environment: Python 3.12.14; NumPy 2.3.5; SciPy 1.17.0.

- Seven unittest checks passed: known UPS totals, invalid/missing items, duplicate IDs, education eligibility, constant variables, known negative rank correlation and seed repeatability.
- The ten-row synthetic benchmark completed and generated both scored.csv and results.json.
- All 1,000 bootstrap resamples were valid in the smoke test.
- Runtime was approximately 0.4 seconds in the preparation environment; this is not a performance requirement.
- Tests and benchmark used the already-installed exact package versions. Fresh dependency installation was not tested.
- Docker was unavailable; docker build has not been tested.
- No main-sample hypothesis test, raw-data sensitivity analysis or adjusted model has been performed.
- Public GitHub repository and actual author contribution history remain to be created by the pair.
