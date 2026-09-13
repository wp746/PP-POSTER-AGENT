---
name: event-kv-poster
description: Use when a user wants activity, event, campaign, membership, forum, exhibition, cultural, tourism, competition, hackathon, or brand KV posters from text, images, logos, IP assets, PDFs, PPTs, Word files, or links, especially when selecting or auto-routing among P01-P18 poster styles.
---

# Event KV Poster

## Overview

Use this skill to turn mixed event materials into production-ready KV prompts while preserving source truth. The skill is provider-neutral: the host supplies multimodal extraction and an image-generation adapter.

## Required behavior

1. Read every user-provided source that materially affects the poster. Extract hard facts and brand assets before art direction.
2. User instructions override defaults: requested P-style, ratio, copy, asset use, output count, language, and must-include/must-avoid constraints win.
3. Never invent phone numbers, addresses, dates, prices, prize amounts, organizers, certifications, venues, or other hard facts.
4. If style is unspecified, route to one P01-P18 style using activity type, information density, available people/space/product assets, brand tone, and communication goal. Read `references/style-library.md`.
5. Default output: exactly **3 independent posters**, **9:16**, **4K final pixels (2160×3840)**. Never return a collage, triptych, contact sheet, nine-grid, or multiple proposals in one canvas.
6. The 3 default variants remain inside one selected P-style: A context/region-grounded, B activity-core, C concept-creative. Use geography only when relevant; never force landmarks.
7. Generate each variant with a separate prompt/call when possible. Reference images must retain their real role (logo, IP, person, product, venue, interior).
8. If visual QC is available, check: single-canvas output, target ratio, selected style, major required copy, and obvious fact drift. Allow at most one targeted repair regeneration per failed variant.
9. Final copy edits should preserve approved design unless the user asks for a new direction.

## Portability

Read `references/provider-contract.md` for the minimum multimodal/image API adapter and `references/io-schema.md` for normalized input/output. Keep credentials outside prompts, chat, files, and Git.
