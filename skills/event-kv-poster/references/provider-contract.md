# Provider Contract

The skill does not own credentials or a specific vendor. The host must supply these capabilities.

## Multimodal extractor

`analyze(materials) -> brief`

- Inputs: text; parsed PDF/PPT/DOCX text; public/signed image URLs or image bytes; optional webpage text; asset roles when known.
- Output: normalized factual brief matching `io-schema.md`.
- Must distinguish observed facts from inference. Missing hard facts remain empty.

## Image generator

`generate(prompt, reference_images, aspect_ratio) -> image`

- One call represents **one complete poster canvas**. Never ask one call to return a nine-grid/contact sheet.
- Preserve asset identity for logos, IP, people, products, and venues.
- If the provider supports edits/reference images, use that mode when references exist.
- For the default three outputs, compile three independent prompts (A/B/C) and call the provider separately when possible.

## Final pixels

Default final deliverable is 2160×3840 for 9:16. If the provider only renders smaller native images, upscale/post-process after generation; do not claim native 4K. Suggested other targets: 3840×2160 for 16:9 and 3072×3072 for 1:1.

## Optional visual QC

`evaluate(image, brief, style, ratio) -> {pass, feedback}`

Hard-gate only obvious delivery failures: collage/multiple panels, wrong orientation, selected-style collapse, missing/incorrect major required copy, obvious source-truth drift. Allow at most one targeted repair regeneration for a failed variant. Provider/QC protocol failures do not justify infinite regeneration.

## Security

Keep API keys in secret stores/environment variables. Never commit them to the Skill or insert them into prompts. Validate fetched URLs against SSRF/private-network access before server-side retrieval.
