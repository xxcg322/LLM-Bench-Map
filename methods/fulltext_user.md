Read the supplied exact-version paper. Return JSON with these keys:

- `schema_version`: "final-instrument-first-v6.1"
- `document_version_id`: copy the supplied document ID exactly
- `benchmark_release`: "yes", "no", or "unclear"
- `target_scope`: "llm_only", "mixed_or_non_llm", or "unclear"
- `tags`: the seven-field object only when benchmark_release is "yes" and
  target_scope is "llm_only"; otherwise null

The seven tag keys are target_system, evaluation_domain, evaluation_setup, modality,
material_origin, scoring_source, and task_language. Use defined enum arrays;
for task_language use the canonical language codes or sentinels defined above.
Do not return paper_role, names, reasons, evidence, confidence, or extra keys.
