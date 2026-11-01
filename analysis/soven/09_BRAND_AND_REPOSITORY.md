# SOVEN brand and repository delivery

The product name is SOVEN and the repository slug is soven. The owner selected a minimal S/page/voice identity. Three generated concepts were reviewed; concept A was selected for its compact silhouette and clear page fold. The production master is newly constructed editable SVG geometry, not a raster image wrapped in SVG.

## Logo system

assets/brand/soven contains the primary transparent SVG/PNG, warm-white presentation, dark presentation, monochrome and white lockups, standalone symbols, app icon, favicon-scale exports, quality sheet and repository banner. frontend/public/brand contains the files consumed by the app; frontend/app contains favicon and application icons. Keep corresponding copies synchronized when the master changes.

The primary mark uses indigo #4338CA and teal #0F766E with ink #15202B and paper #FAF8F4. On dark backgrounds use the light-indigo #A5B4FC and mint #5EEAD4 variant. The wordmark is uppercase with deliberate spacing and editable text. Its SVG font stack uses DM Sans, Segoe UI and Arial; PNG exports provide fixed appearance when those fonts differ. Self-hosted application fonts retain their upstream licensing.

Maintain clear space of at least one quarter of the symbol width. Use the standalone app icon at small sizes, not a tiny full wordmark. Do not stretch, outline, rotate, add glow or place low-contrast versions on patterned backgrounds. Monochrome use preserves the page-fold gap. Logo assets are not evidence of Meta sponsorship or a clinical accreditation.

The original image-generation concepts are in brand-concepts for review and provenance. Their warm-white bitmap backgrounds are not claimed to be transparent. Final transparent assets are rendered from the native vector master. The built-in image-generation tool was used for concept exploration; editable geometry and deterministic exports form the delivered identity.

## Repository packaging

Target repository: https://github.com/Waleed-Khalid-dev/soven. It is public, independent and starts with a reviewed baseline commit followed by branding/documentation. The old TeamXOF repository is not renamed or overwritten. The MIT license and copyright remain intact; README acknowledges the source project and distinguishes inherited repairs from new SOVEN work.

Include active source, fonts, necessary data, supported tests, CI, setup examples and this handoff. Exclude private environments, credentials, databases, backups, raw recordings, model weights, dependencies, builds, logs, personal telemetry, original planning files and oversized historical decks/videos/executables. Inspect exact staged contents before push; an ignore file alone does not remove an already tracked secret.

Visible app identity, metadata, logo and launch entry point use SOVEN. Technical contexts, API fields, database names, browser storage keys and real provider labels remain compatible. Internal SpeakFlow identifiers are documented legacy names rather than misleading product branding. Future provider migration must change actual behavior, not only labels.

## Publication and maintenance

The README banner is an actual repository file, and topics/description identify the current reading platform. GitHub's optional custom social-preview setting is separate from the README banner and may require an available authenticated UI; do not claim it is set without verification. No deployment URL is invented.

Publication state, commits, exact remote SHA and CI links belong in DELIVERY_STATUS.json. Validation results belong in VALIDATION_RESULTS.json. After subsequent edits refresh the source catalogue and document hashes. Review image sizes, local links, omitted private categories and fresh-checkout setup whenever packaging changes.
