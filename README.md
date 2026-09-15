# LLM-Bench-Map

Data and reproducible analysis code for **What Do We Expect from LLMs? Mapping the
Design of LLM Benchmarks**, by Chao Wang, Independent Researcher.

The dataset maps **14,767 arXiv papers** introducing or updating LLM evaluation
resources, first submitted from January 2022 through August 2026. It describes what
systems and domains are tested, the evaluation materials and conditions, and how
success is scored. It measures published benchmark designs, not adoption or quality.

Repository: [xxcg322/LLM-Bench-Map](https://github.com/xxcg322/LLM-Bench-Map).

## Browse the data

| File | Contents |
| --- | --- |
| [data/papers.csv](data/papers.csv) | 14,767 included paper records with seven multi-label fields |
| [data/inputs/paper_index.csv](data/inputs/paper_index.csv) | Titles, exact arXiv versions and decisions for all 16,376 processed candidates |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Fields, missing values and denominators |
| [data/OVERVIEW.md](data/OVERVIEW.md) | Readable field counts and matched-year comparisons |
| [data/tables/](data/tables/) and [data/figures/](data/figures/) | Base analysis tables, figures and their numerical source data |
| [expected/](expected/) | Full-year/matched-month comparisons and error-sensitivity scenarios |
| [methods/](methods/) | The actual screening and coding prompts, schemas and M0 specification |

Each row represents a paper, not a deduplicated benchmark family. Of the included
records, 14,736 have complete coding and 31 have one or more invalid fields.
Invalid fields are excluded only from calculations requiring those fields.
First-submission dates define the cohorts; labels describe the particular version
read. See [analysis methods](data/METHODS.md) for the statistical conventions.

The study corpus is documented by the data files, not by a reference list containing
every included paper. Sources can be located using their exact arXiv IDs in the index.

## Reproduce

With Python 3.11 or later, run from the repository directory:

```sh
python -m pip install -r requirements.txt
python reproduce.py
```

**No LLM API key, paid call, PDF download or network connection is needed after
installing dependencies.** The script checks file integrity, rebuilds the analyses
in a temporary directory and compares numerical results with the supplied outputs.
To keep the regenerated files, use a new output directory:

```sh
python reproduce.py --output reproduced
```

For a quick file-integrity check only:

```sh
python reproduce.py --verify-only
```

Existing output directories are never overwritten. Do not use Python's `-O` option;
it disables assertions used by the numerical checks. UTF-8 text checks allow only
Windows/Unix line-ending differences. Binary archives are checked byte-for-byte.
Figure rendering may vary with fonts or library versions; the plotted CSV values
are included in the numerical comparison.

## Scope and limitations

The release reproduces analyses from the completed coding results, **not** upstream
arXiv collection, M0 training or LLM inference. Those stages are documented in
`methods/`, but the full metadata frame, M0 training data/weights and API receipts
are not bundled. PDFs, source full text and model reasoning traces are not included.

Selection and automated coding can introduce error. Computational reproduction
does not establish semantic accuracy or complete coverage. The sensitivity scenarios
use assumed error budgets, not measured error rates. Selected development findings
in `diagnostics/` are not an independent accuracy sample.

The figures are analysis outputs; the manuscript may use more compact layouts
with the same numbers. [PROVENANCE.json](PROVENANCE.json) records source hashes and
publication transformations; [RELEASE_MANIFEST.json](RELEASE_MANIFEST.json) checks
the contents of this package.

## Citation and licenses

Please cite Chao Wang, *What Do We Expect from LLMs? Mapping the Design of LLM
Benchmarks* (2026), and link to this repository when using the data or code.
Machine-readable metadata is provided in [CITATION.cff](CITATION.cff).

- Original code: [MIT](LICENSE).
- Original annotations and aggregate data: [CC BY 4.0](LICENSE-DATA.md).
- Third-party paper metadata and other third-party material retain their existing
  rights; see [LICENSING.md](LICENSING.md).
