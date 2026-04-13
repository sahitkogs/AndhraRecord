# Data License — Open Database License 1.0

**The datasets, database contents, surname directories, classification outputs, and other collections of structured records published by *The Amaravati Record* are licensed under the Open Database License 1.0 (ODbL).**

Copyright © 2026 Sahit Koganti / The Amaravati Record.

Full license text: <https://opendatacommons.org/licenses/odbl/1-0/>
Human-readable summary: <https://opendatacommons.org/licenses/odbl/summary/>

## What ODbL is, in plain English

ODbL is the industry-standard license for openly-published databases. It is what **OpenStreetMap** uses. It carves out legal protections for databases that plain Creative Commons licenses do not handle cleanly (specifically, the "sui generis database rights" recognized in the EU Database Directive and, increasingly, in national law).

## What you are free to do

- **Share** — copy, distribute, and use the database.
- **Create** — produce works from the database, including by combining it with other data.
- **Adapt** — modify, transform, and build upon the database.

All of these, including for commercial purposes.

## Under the following three terms

### 1. Attribution

You must attribute any public use of the database, or works produced from the database, in the manner specified below. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.

### 2. Share-Alike

If you publicly use any **adapted version** of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.

**Plain English:** if you take our cleaned surname directory, add 5,000 new entries, and publish the combined database, you must publish your combined database under ODbL too. This prevents a commercial scraper from building a proprietary database on top of our work without contributing back.

### 3. Keep open

If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.

## Required attribution format

When publishing data derived from our datasets, credit as:

> Contains data from *The Amaravati Record*, licensed under ODbL 1.0.
> Source: https://sahitkogs.github.io/TheAmaravatiRecord/

For academic citation:

> Koganti, S. (2026). *Amaravati Land Pooling Scheme beneficiary database* [Data set, ODbL 1.0]. The Amaravati Record. https://sahitkogs.github.io/TheAmaravatiRecord/

## What counts as "a database" under this license

- The full APCRDA beneficiary roll after cleaning and deduplication
- The surname-to-caste directory
- The Gemini per-name classification outputs
- The village-level aggregation tables
- Any CSV, JSON, Parquet, or other structured file published alongside a report
- The **contents** of interactive dashboards (the underlying numbers), as distinct from the visualization code

**Individual facts** extracted from a database (for example, "Village X has N plots") are not themselves protected — you can quote a single number from our report under fair use without ODbL obligations. The ODbL kicks in when you reuse enough of the structured data to constitute a "substantial" portion of the database.

## Collective vs. produced works

- A **collective work** (our database sitting alongside other data in a collection) only requires attribution, not share-alike.
- A **produced work** (a chart, map, or report derived from the database) only requires attribution, not share-alike — but the database used to produce it must itself be made available under ODbL.
- An **adapted database** (our database modified, filtered, joined, or extended) must be released under ODbL if it is made public.

This tripartite distinction is the core of ODbL and is why it is the standard choice for data publishers who want maximum reuse without losing open-data guarantees.

## Notices and disclaimers

- **No warranty.** The database is provided "as is." We make no representation about its accuracy, completeness, or fitness for any particular purpose. Caste classification is an approximation, not a census — see the methodology page for detailed caveats.
- **Moral rights** retained by the author are not affected.
- **Personal data** in the source datasets has been masked or aggregated before publication in accordance with our privacy policy. If you encounter personally-identifying information in our published datasets, please report it to <sahit.koganti@gmail.com>.

## What this license does NOT cover

- **Prose, analysis, interpretation, and editorial commentary.** Those are licensed under CC BY 4.0. See [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md).
- **Source code of scrapers, classifiers, and build tooling.** That is licensed under the MIT License. See [`LICENSE-CODE.md`](LICENSE-CODE.md).
- **Upstream public data from APCRDA, MyNeta, and community surname lists** — those are used under their own terms (typically public-domain or fair-use-for-research), which are not affected by our downstream ODbL license on our cleaned derivative.

---

*This license applies to all databases published by The Amaravati Record from its founding edition (April 2026) onward. See [`LICENSE.md`](LICENSE.md) for the full three-layer license stack.*
