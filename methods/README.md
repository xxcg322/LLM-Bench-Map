# Screening and coding instructions

- `metadata_prompt.txt` and `metadata_schema.json`: abstract-level triage. Only
  valid records with `p=B` and `t=L` proceed to full text; undetermined outputs are
  not routed.
- `fulltext_prompt.md`, `fulltext_user.md` and `fulltext_schema.json`: the actual
  final full-text eligibility and seven-field coding instructions.
- `m0_freeze.json`: the historical specification of the retained local ranker.
  Its training-era primary-purpose wording does not replace the later
  instrument-based eligibility definition in the actual screening prompts.
  Its validation requirements describe the historical freeze-time plan, not
  additional steps required to reproduce this release.

Both abstract screening and final coding used the provider model identifier
`glm-5.3-flash`. Final requests used high reasoning effort, disabled sampling,
structured JSON, a 3,200-token output limit, and a 1,000,000-byte UTF-8 input guard.
The identifier does not freeze provider weights or guarantee identical future
responses. `python reproduce.py` uses archived outputs and makes no model calls.

These files preserve the original source bytes, including scientific version names
and hashes. Paths inside the M0 specification identify its original archive; they
are not dependencies for `python reproduce.py`. Training weights and the complete
upstream metadata frame are outside the scope of this analysis release.
