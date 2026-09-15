# Data dictionary

## Record identity and decisions

`document_id` identifies the exact arXiv version. `first_submission_month` and
`first_submitted_at` date the first submission, not the design's original release.
`version_submitted_at` dates the version read. Titles are available in the full-text
candidate index. One record per paper; benchmark-family deduplication is not implied.

`decision`: `included` and `included_partial_labels` enter the analysis. Other
decisions remain in the candidate index for inspection and flow accounting. A source
download failure is not a scientific rejection; the 52 unavailable sources lie outside
this 16,376-record index.

## Seven multi-label fields

| Field | Question |
| --- | --- |
| `target_system` | Does the model answer, act through tools, or control a body? |
| `evaluation_domain` | Which subject or application does the evaluation explicitly target? |
| `evaluation_setup` | Are tasks fixed, generated at run time, or interactive? |
| `modality` | Which input/output modalities are part of the evaluation? |
| `material_origin` | What sources or generators produce the evaluation material? |
| `scoring_source` | What determines the official score or outcome? |
| `task_language` | Which task languages are explicitly supported by the paper? |

Exact enumerations and boundaries are in `methods/fulltext_schema.json` and
`methods/fulltext_prompt.md`; those frozen instructions, rather than this short
orientation, define the coding. The user-message template is also included.

CSV label cells are JSON arrays; a blank cell denotes an invalid/missing field.
In the structured JSON results, this is represented by `null`, not an empty set.
Special labels such as `unclear`, `not_reported` and
`multilingual_unspecified` preserve reported uncertainty. An unselected label does
not establish real-world absence. Arrays are multi-label, so percentages can exceed
100% when summed. General/cross-domain and specific domains may coexist.

For each field the denominator is included records with valid coding. Cross-field
statistics require the relevant fields to be valid. Domain slices overlap. Additional
known-only summaries exclude applicable sentinel states. Small groups are flagged;
they should not be presented as strong trend evidence.

`data/inputs/results.json.gz` contains derived structured coding records, not PDF
text or model reasoning. It includes field validation status as well as the model's
structured label payload. Preserve invalid-field information when reusing the data.
