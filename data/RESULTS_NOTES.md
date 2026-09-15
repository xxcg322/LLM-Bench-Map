# Results guide

These findings describe the identified literature.

## C01 - scope

The analysis includes 14,767 paper records, not 14,767 independent benchmark families.

Data: `papers.csv; flow.json`. Selector: `included + included_partial_labels`.

Selection error and family duplication are not fully quantified; counts do not measure adoption.

## C02 - RQ3

LLM scoring rises from 433/1,681 (25.8%) to 2,309/5,734 (40.3%) in the matched January-August windows.

Data: `tables/label_rates.csv; figures/fig4_scoring_data.csv`. Selector: `jan_aug; 2024/2026; scoring_source=llm_judge`.

These are coded design shares, not changes in scoring reliability.

## C03 - RQ3

Of the 14.51 percentage-point increase, agent composition contributes 0.56 and within-group change 13.95.

Data: `design_analysis.json; tables/decompositions.csv`. Selector: `primary; outcome=llm; strata=[agent]; start=2024; end=2026`.

A symmetric arithmetic allocation under this grouping, not a causal effect.

## C04 - RQ2xRQ3

Across the full window, 3,272/14,763 (22.2%) combine generated materials with LLM scoring.

Data: `roles.json; figures/fig5_material_scoring_data.csv`. Selector: `generated_and_llm_judge_n / valid_n`.

Different roles can involve different models, components or evaluation stages.

## C05 - RQ2xRQ3

Within this intersection, 2,530/3,272 (77.3%) also use human/real-world materials and 2,020/3,272 (61.7%) additional scoring mechanisms.

Data: `roles.json; figures/fig5_material_scoring_data.csv`. Selector: `within_llm_intersection; conditional denominator=3272`.

These categories overlap; mixed design does not establish oversight or quality.

## C06 - RQ2xRQ3

Joint prevalence increases, but lift changes from 1.32 to 1.22; an increasingly strong association is not established.

Data: `tables/associations.csv; design_analysis.json`. Selector: `primary; 2024/2026; lift and joint_changes`.

Association strength is distinct from changes in the two marginal shares.

## C07 - RQ2

English-only coding changes from 1,332/1,677 (79.4%) to 4,723/5,728 (82.5%).

Data: `tables/language_summary.csv; design_analysis.json`. Selector: `jan_aug; all groups; en_only; 2024/2026`.

Language coverage is a secondary result; absent tags do not prove unsupported languages.

