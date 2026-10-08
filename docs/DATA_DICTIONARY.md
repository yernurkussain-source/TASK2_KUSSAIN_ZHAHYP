# Data dictionary and preparation rules

One row represents one respondent. The sample CSV is entirely synthetic. Field order must match the example exactly.

| Field | Rule |
| --- | --- |
| record_id | Unique generated ID; do not use participant initials |
| age | Numeric age >=18; ambiguous source entries such as 23+ must be documented separately before exact-age adjustment |
| education | bachelor_category or master_category; these labels include graduates/current students |
| ai_frequency | 1: A few times a month; 2: Once a week; 3: A few times a week; 4: Everyday |
| ups_1 through ups_6 | Source workbook columns 28–33 (one-based), in their original order |

UPS mapping after trimming spaces and converting case: Do not agree = 1; Agree slightly = 2; Agree moderately = 3; Agree very much = 4. All six supplied items point in the same direction; no reverse scoring is applied. Sum all six; no prorating or zero imputation. Audit confirmed this mapping reproduces all 300 supplied cleaned totals.

Do not treat the mixed-format nine-item AI composite as the primary predictor. One item uses daily hours whereas others use frequency, and the downloaded nine-item adaptation differs from the referenced eight-item scale.

Main source: supplied cleaned workbook, excluding Higher Secondary and age below 18. Observed category counts for 285 records: monthly 81, once weekly 39, several times weekly 129, daily 36. This is an eligibility audit, not an association result.

The raw-data sensitivity analysis must explain exclusions, distinguish Rarely/Never from missing values, and document age normalization. Do not silently copy the authors' undocumented selection. A raw-data preprocessing script is not included at this stage.
