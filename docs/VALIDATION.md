# Validation record

Date: 2026-10-07
Environment: Python 3.12.14; NumPy 2.3.5; SciPy 1.17.0.

- Seven unittest checks passed: known UPS totals, invalid/missing items, duplicate IDs, education eligibility, constant variables, known negative rank correlation and seed repeatability.
- The ten-row synthetic benchmark completed and generated both scored.csv and results.json.
- All 1,000 bootstrap resamples were valid in the smoke test.
- Runtime was approximately 0.4 seconds in the preparation environment; this is not a performance requirement.
- Initial Linux checks used already-installed packages. Fresh dependency installation was subsequently verified on Windows; see the additional validation record below.
- Docker was unavailable; docker build has not been tested.
- No main-sample hypothesis test, raw-data sensitivity analysis or adjusted model has been performed.
- The GitHub repository has been created and published. Commit history records changes from both collaborators: https://github.com/yernurkussain-source/TASK2_KUSSAIN_ZHAHYP

## Additional Windows validation — 2026-10-08

- Environment: Windows, Python 3.13.7, NumPy 2.3.5, SciPy 1.17.0.
- Dependencies installed successfully in a virtual environment.
- All seven unit tests passed.
- The synthetic sample benchmark completed successfully.
- Reported invalid records, missing required values and duplicate IDs: 0.
- Observed runtime: 0.423 seconds.
- Docker build remains unverified.
- These checks validate the software pipeline, not the research hypotheses.

## Docker validation — 2026-10-11

- Host: Windows with Docker Desktop, Linux containers.
- Docker CLI version reported before execution: 29.8.2.
- Image build completed successfully, including the unit-test step.
- Container environment: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0.
- Synthetic sample: 10 records.
- Valid bootstrap resamples: 1,000; skipped: 0.
- Invalid records, missing required values and duplicate IDs: 0.
- Benchmark runtime: 0.6274 seconds on this machine.
- Container exit code: 0.
- This check confirms pipeline execution, not research findings.
- This result supersedes the earlier notes that Docker verification was pending.
