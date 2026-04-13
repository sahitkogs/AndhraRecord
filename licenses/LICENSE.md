# Licensing

**The Amaravati Record** publishes three kinds of asset, and each carries a different license. This is the industry-standard stack for data journalism — it mirrors what OpenStreetMap, Our World in Data, ProPublica, and most serious independent newsrooms do.

| Asset | License | File | TL;DR |
|-------|---------|------|-------|
| **Prose, articles, reports, HTML pages** | Creative Commons Attribution 4.0 International (CC BY 4.0) | [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) | Reuse freely, even commercially. Just credit *The Amaravati Record* and link back. |
| **Datasets and database contents** (CSVs, classification outputs, surname directory) | Open Database License 1.0 (ODbL) | [`LICENSE-DATA.md`](LICENSE-DATA.md) | Reuse freely. If you publish a derivative database, release it under ODbL too. Credit required. |
| **Source code** (scrapers, classifiers, build scripts, site assets) | MIT License | [`LICENSE-CODE.md`](LICENSE-CODE.md) | Do whatever you want. Keep the copyright notice. No warranty. |

## Which license applies to a given file?

- Files under `docs/`, the text of any report, and any hand-written narrative (`*.html`, `*.md` that contain prose) → **CC BY 4.0**
- Files under `data/`, `explorer/surname_ground_truth.csv`, `docs/reports/*.html` insofar as they embed dataset values → **ODbL 1.0**
- Files ending in `.py`, `.js`, CSS, build scripts, and template engines → **MIT**

When a single file mixes categories (for example, a report HTML that is both prose *and* a dataset visualization), the **most permissive** applicable license governs — in practice this means CC BY 4.0 for mixed content, because CC BY and ODbL are compatible for derivative databases as long as you preserve attribution.

## Attribution format

When reusing content or data, please credit as follows:

> Sahit Koganti / *The Amaravati Record* — <https://sahitkogs.github.io/TheAmaravatiRecord/>

For academic citation:

> Koganti, S. (2026). *[Report title].* The Amaravati Record. Retrieved from https://sahitkogs.github.io/TheAmaravatiRecord/

## Commercial use

All three licenses **permit commercial use**. You do not need to ask permission, pay a fee, or sign anything to republish, translate, quote, or adapt the work. The only obligation is attribution (and, for databases, share-alike on derivatives).

If you are a news organization commissioning original work or an institution that requires a bespoke data-license agreement for procurement reasons, contact the editor at <sahit.koganti@gmail.com>.

## Why this stack?

- **CC BY 4.0** maximises reach. The Markup, ProPublica, Rest of World, Bellingcat, and most public-interest data-journalism outlets use CC BY because impact matters more than exclusivity.
- **ODbL 1.0** is the standard database license: it carves out sui-generis database rights (which CC BY does not handle cleanly) and applies a share-alike obligation to database derivatives, preventing a commercial scraper from building a proprietary moat on top of a publicly-funded dataset.
- **MIT** is the frictionless default for code. It does not force downstream users to open-source their own code, which lowers the barrier for other journalists and researchers to adopt the pipeline.

---

*Last updated: April 2026. This license stack applies to all work published by The Amaravati Record from its founding edition onward. Earlier drafts and unreleased code fragments in the repository history may not carry an explicit license — contact the editor if you need to reuse them.*
