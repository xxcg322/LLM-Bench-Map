# Error-sensitivity scenarios

The scenarios compare January-August 2024 and 2026. They use assumed maximum
error budgets per year and binary label, not measured error rates or confidence
intervals. `scenarios.csv` provides all 200 combinations of measures and scenarios.

| Measure | Observed change (percentage points) | Range with at most 5% label errors per year |
| --- | ---: | ---: |
| Agent/tool systems | +19.29 | +9.31 to +29.27 |
| Interactive evaluation | +18.66 | +8.68 to +28.64 |
| LLM scoring | +14.51 | +4.53 to +24.49 |
| Execution/environment scoring | +11.55 | +1.56 to +21.53 |
| Fixed task collections | -0.75 | -10.01 to +9.23 |
| Generated materials | +1.81 | -8.17 to +11.79 |
| English-only coding | +3.03 | -6.92 to +12.97 |

The four larger changes retain their direction under this assumption. This does
not show that actual errors are below 5%. Smaller changes and domain-share
movements are more sensitive; all domains are included in the scenario table.

The separate ineligible-removal scenarios allow the removed records to be
concentrated on the most adverse label side. Neither scenario covers upstream
omissions, group-label error or joint effects of multiple error processes.

Selected development checks identified possible interaction and language omissions
in final coding. They are retained in `diagnostics/` as development evidence, not
an independent accuracy estimate. The final dataset is not silently corrected from
those cases. These checks do not establish the prevalence of similar errors.

The script independently reconciles 38 published label rates and checks the
English-only counts. Both bound formulas are verified by exhaustive enumeration
for populations of 2-14 records. Run `python reproduce.py` at the repository root.
