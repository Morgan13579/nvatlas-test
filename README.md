# NVAtlas — words in motion

A static English / Traditional Chinese corpus explorer for the 2026R1 Translation Technology final project.

## Run locally

No packages, build step, backend, database or CDN required:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Visit http://127.0.0.1:8765. Direct `file://` opening cannot fetch the JSON dataset.

## Features

- `index.html`: English/Chinese keyword search, category/checking filters, duplicate/content controls, linked network, treemap, bilingual KWIC, scatter plot, sortable/paginated table, filtered CSV export.
- `report.html`: bilingual report with all eight required sections and evidence-based draft analysis.
- `codebook.html`: five provisional categories with theory reference, decision rules, positive/negative examples, boundary cases, pilot and revision log.
- `ai.html`: declaration with actual prompts, responsibilities, and a documented AI rule error.
- `about.html`: provenance, downloads and manual-check instructions.

URL parameters preserve every filter, selected record, graph controls, sorting, pagination and language. One shared filtered dataset feeds all charts and the grid. Network display limits and the 20-row KWIC preview have explicit coverage captions; they do not silently change the corpus filters. Top statistics describe the complete input file.

## Data and remaining student work

The original CSV is preserved: **500 records, 492 distinct pairs, eight duplicate records**, 195 English labels, 282 Chinese labels. All human-check flags are **no**, as confirmed by the student. Six records are conservatively flagged for potentially sensitive content and hidden by default. Full downloads include them; keyword screening is not exhaustive.

Original source, corpus version, licence, collection date, sampling method and source-ID meanings are unknown. No provenance, translations or personal checking were invented. Do not submit this as a verified or representative corpus. Personal report sections and codebook definitions need student revision.

Before submission, establish traceable sources and permission, document original sampling, verify at least 50 entries, review the codebook pilot, and write personal motivation/reflection. If 500 distinct pairs are required, obtain at least eight additional permitted, traceable examples; do not synthesize them.

## Regenerate and annotate

```sh
python3 scripts/build_data.py
```

`data/provenance.json` holds corpus-level metadata. Put actual checking results in `data/annotations.csv`, keyed by original `id`. A `human_checked=yes` row requires `source`, `checked_date`, and checking `notes`; add `source_url` wherever available. Unknown/duplicate IDs and invalid status/categories fail validation. Text corrections go in the original CSV with a documented Git change and report entry.

The generator emits normalized JSON/CSV and two worksheet templates. Keep completed worksheets separately: templates are regenerated. The manual-review sample uses Python `random.Random(20261105).sample()` for 50 distinct pairs without replacement; the pilot uses `20261104` for 25. Population order follows the input. These are review seeds, **not original collection seeds**. Frozen IDs and input SHA-256 are in `data/corpus.json`. Preserve previous JSON and completed sheets if input changes, because samples can change.

## Verify

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/core.test.mjs
```

Tests cover original text preservation, required fields, deterministic samples, duplicate sensitivity, annotation regressions, bilingual/compound search, aggregate counts, URL state, sorting, escaping and spreadsheet-safe export.

## Publish and architecture

Push to `main`. GitHub Settings → Pages → Deploy from a branch → main → / (root). `.nojekyll` enables direct static serving. Intended URL: https://morgan13579.github.io/nvatlas-test/.

`assets/core.mjs` contains pure filter/aggregate/URL/export functions, `app.mjs` renders the explorer, `content.mjs` contains bilingual report/codebook copy, and CSS files handle presentation. `scripts/build_data.py` normalizes the data. No credentials or coursework PDF are redistributed.

Theory reference: Vinay & Darbelnet (1995), *Comparative Stylistics of French and English*, https://benjamins.com/catalog/btl.11. The five operational construction categories are specific to this project, not the book's taxonomy.
