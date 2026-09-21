# Changelog

## [0.45.0](https://github.com/scenario-labs/skills/compare/skills-v0.44.0...skills-v0.45.0) (2026-09-21)


### Features

* **scenario-3d:** cover Astra 3D's fit and cost levers, the parts lane, and game-readiness ([#141](https://github.com/scenario-labs/skills/issues/141)) ([75d8a7a](https://github.com/scenario-labs/skills/commit/75d8a7aa5356916c8ce060857bb4a3a7cd5cd48b))
* **scenario-audio:** teach the song-extend lane, the stems gap, and per-member seed and batch ([#142](https://github.com/scenario-labs/skills/issues/142)) ([60b6b6d](https://github.com/scenario-labs/skills/commit/60b6b6dec00243988cd326f1f1cce6775ec0a409))
* **scenario-image:** teach landing an exact pixel size, and the blur and literalness fixes ([#140](https://github.com/scenario-labs/skills/issues/140)) ([985465b](https://github.com/scenario-labs/skills/commit/985465bfd6d251840760d078f645e107270504e6))
* **scenario-patina-retexture:** add the PATINA retexture and comparison skill ([#137](https://github.com/scenario-labs/skills/issues/137)) ([7f3e506](https://github.com/scenario-labs/skills/commit/7f3e5064ff6c397774b2eec2bb2eae1ac2f38173))
* **scenario-video:** teach duration floors, frame-anchor rules, reference audio, LoRAs, and retirements ([#143](https://github.com/scenario-labs/skills/issues/143)) ([1d1caf4](https://github.com/scenario-labs/skills/commit/1d1caf4219cb590648eab623b21b2afaaf5df42b))


### Bug Fixes

* **scenario:** clarify quota recovery and asset delivery ([#139](https://github.com/scenario-labs/skills/issues/139)) ([8753a54](https://github.com/scenario-labs/skills/commit/8753a5459afa808a815583a633ac97d4cdf8ea14))

## [0.44.0](https://github.com/scenario-labs/skills/compare/skills-v0.43.0...skills-v0.44.0) (2026-09-18)


### Features

* **scenario-video:** teach the lipsync lane: footage or still, face preflight, gating, and verifying the mouth moved ([#121](https://github.com/scenario-labs/skills/issues/121)) ([c7a25f5](https://github.com/scenario-labs/skills/commit/c7a25f5697d71c737690068bfd3dbc1c773db7e3))
* **skills:** add reusable isometric and sprite templates ([#124](https://github.com/scenario-labs/skills/issues/124)) ([6a7cf57](https://github.com/scenario-labs/skills/commit/6a7cf57fbc6c89ec2d98fc5e00a8fd420e9a7df6))

## [0.43.0](https://github.com/scenario-labs/skills/compare/skills-v0.42.0...skills-v0.43.0) (2026-09-17)


### Features

* **scenario-admin-analytics:** add cached MCP usage reporting ([#134](https://github.com/scenario-labs/skills/issues/134)) ([b5ebf6f](https://github.com/scenario-labs/skills/commit/b5ebf6f98495ec92c05d3ea6ccc3c1e416d2ae42))
* **scenario-workflow-authoring:** teach migrating a graph built in Weavy, ComfyUI, or another node tool ([#120](https://github.com/scenario-labs/skills/issues/120)) ([e79a388](https://github.com/scenario-labs/skills/commit/e79a3887e1ce50d67fbdd7d9227054074e61dfc9)), closes [#109](https://github.com/scenario-labs/skills/issues/109)

## [0.42.0](https://github.com/scenario-labs/skills/compare/skills-v0.41.1...skills-v0.42.0) (2026-09-16)


### Features

* **scenario-consistency:** add reference-to-video, style-reference, and when-to-train lanes ([#114](https://github.com/scenario-labs/skills/issues/114)) ([9dea74a](https://github.com/scenario-labs/skills/commit/9dea74a4e05110b8da154a33e6654414874902e9))
* **scenario-moderation:** cover video, audio, and IP Detection blocks ([#115](https://github.com/scenario-labs/skills/issues/115)) ([6f8074b](https://github.com/scenario-labs/skills/commit/6f8074bc2a873dab3219dd04e2d05e0a1751e50b))
* **scenario-team-admin:** add the team administration skill ([#118](https://github.com/scenario-labs/skills/issues/118)) ([8d41021](https://github.com/scenario-labs/skills/commit/8d41021b1333fe819b8ba1be14ad955d03d9ffa6))
* **skills:** teach shot direction, in-image copy, and frame chaining across image and video skills ([#119](https://github.com/scenario-labs/skills/issues/119)) ([5d223d9](https://github.com/scenario-labs/skills/commit/5d223d92a0a642ba061373dbe78dfde71544de4a))


### Bug Fixes

* **scenario:** name the catalog tools' argument facts the clean-room runs kept guessing ([#129](https://github.com/scenario-labs/skills/issues/129)) ([4749955](https://github.com/scenario-labs/skills/commit/47499557acbaac68c4a7cb50369255c4f6b77d94))

## [0.41.1](https://github.com/scenario-labs/skills/compare/skills-v0.41.0...skills-v0.41.1) (2026-09-15)


### Bug Fixes

* **scenario-sprite-animation:** verify extractor frame order instead of assuming time order ([#117](https://github.com/scenario-labs/skills/issues/117)) ([9b56fc1](https://github.com/scenario-labs/skills/commit/9b56fc14b726c39d8c906f14b91b9c85e9009b3c))
* **scenario:** name the search target, the api_key_create lane, and the full allowlist request ([#128](https://github.com/scenario-labs/skills/issues/128)) ([c82a963](https://github.com/scenario-labs/skills/commit/c82a963f253c131d73a76bcbdda435d7f1ed04c7))
* **scenario:** teach per-client re-authentication and the first-call failures usage data surfaced ([#116](https://github.com/scenario-labs/skills/issues/116)) ([0af22c0](https://github.com/scenario-labs/skills/commit/0af22c0e6a59414632a73da88dbe5e90a8477b79))
* **skills:** teach the payload errors usage data surfaces: file field names, image-only inputs, list caps, downloads ([#122](https://github.com/scenario-labs/skills/issues/122)) ([ff10d64](https://github.com/scenario-labs/skills/commit/ff10d6432c216b2ab04df66bd2e3d24329700cd0))
* **skills:** verify audio sync after a concat and frame order after an extraction instead of trusting either ([#123](https://github.com/scenario-labs/skills/issues/123)) ([d2a84cf](https://github.com/scenario-labs/skills/commit/d2a84cf5fd78aa06f52dbbd6969aecb0f37b71f9))

## [0.41.0](https://github.com/scenario-labs/skills/compare/skills-v0.40.1...skills-v0.41.0) (2026-09-10)


### Features

* **scenario-gpt-image:** add GPT Image 2.5 Flare and Sunburst with the quality price ladder ([#111](https://github.com/scenario-labs/skills/issues/111)) ([0ad9328](https://github.com/scenario-labs/skills/commit/0ad9328d8065c31e004189fc3d409fed148459bb))
* **scenario-sprite-animation:** add the single-sheet lane with post-alignment, slice and snap-per-tile packaging ([#110](https://github.com/scenario-labs/skills/issues/110)) ([648c9d9](https://github.com/scenario-labs/skills/commit/648c9d95e5bf30ee7f18459c2f27c8bb3eead3a8))


### Bug Fixes

* **skills:** route every wait=false launch to jobs_wait regardless of the status word ([#112](https://github.com/scenario-labs/skills/issues/112)) ([ca1908c](https://github.com/scenario-labs/skills/commit/ca1908c31b965b1b9611be40f812ffe5c598166b))


### Documentation

* **tooling:** link the upstream skills.sh groupings report ([#106](https://github.com/scenario-labs/skills/issues/106)) ([168e668](https://github.com/scenario-labs/skills/commit/168e6682d6cd9f2fd4b6196c1c904aa449048e1a))

## [0.40.1](https://github.com/scenario-labs/skills/compare/skills-v0.40.0...skills-v0.40.1) (2026-09-02)


### Bug Fixes

* **scenario-model-training:** launch training only through start after an approved dry-run quote ([#103](https://github.com/scenario-labs/skills/issues/103)) ([75e68f9](https://github.com/scenario-labs/skills/commit/75e68f9a5078ba9a137e33e949d5daa31d8a2d79))

## [0.40.0](https://github.com/scenario-labs/skills/compare/skills-v0.39.0...skills-v0.40.0) (2026-09-02)


### Features

* **scenario-caption-studio:** teach video captioning with Caption Studio ([#97](https://github.com/scenario-labs/skills/issues/97)) ([4fde0cc](https://github.com/scenario-labs/skills/commit/4fde0cc643e8919ee84e6d874904f9ce802b78ed))


### Bug Fixes

* **skills:** route capability discovery through recommend, name the fixed platform tools, and close validated gaps ([#100](https://github.com/scenario-labs/skills/issues/100)) ([afb4408](https://github.com/scenario-labs/skills/commit/afb44086affb74b635f2724d63791a80e330555f))

## [0.39.0](https://github.com/scenario-labs/skills/compare/skills-v0.38.0...skills-v0.39.0) (2026-09-01)


### Features

* **agents:** audit discovery misuse in pr-handle and align maintainer surfaces on recommend-first discovery ([#99](https://github.com/scenario-labs/skills/issues/99)) ([e0a61d5](https://github.com/scenario-labs/skills/commit/e0a61d5ca820c1bee41b52106756bb46a202afad))
* **scenario-brand-kit:** add brand kit skill for editable-SVG visual identities ([#92](https://github.com/scenario-labs/skills/issues/92)) ([32b9e2b](https://github.com/scenario-labs/skills/commit/32b9e2b197a58dcf24e80bfd8333deb565e9fe45))

## [0.38.0](https://github.com/scenario-labs/skills/compare/skills-v0.37.3...skills-v0.38.0) (2026-08-31)


### Features

* **skills:** add scenario-ugc and scenario-fan-cam, with the discovery and filing rules they proved out ([#91](https://github.com/scenario-labs/skills/issues/91)) ([c703659](https://github.com/scenario-labs/skills/commit/c70365922199a91b81831e1638c376ed9a7dea11))

## 0.37.3 (2026-08-28)


### Features

* **ci:** adopt release-please and publish release notes to the Scenario changelog ([#89](https://github.com/scenario-labs/skills/issues/89)) ([ec9542a](https://github.com/scenario-labs/skills/commit/ec9542a5743845207c6592b98b6e0f3b05bbf85a))


### Bug Fixes

* **scenario-sprite-animation:** route alpha through the removal pass the video lane forces ([#87](https://github.com/scenario-labs/skills/issues/87)) ([2442874](https://github.com/scenario-labs/skills/commit/2442874f7d9d4544fbfedcd74803cc3c2c81c2f9))
* **skills:** name the direct tools and the resize surface agents kept missing ([#95](https://github.com/scenario-labs/skills/issues/95)) ([57a6afe](https://github.com/scenario-labs/skills/commit/57a6afe6b6ff7245a9fb46fa18a2330a480f642c))
* **skills:** teach the resize fit parameter and retire preserveAspectRatio ([#85](https://github.com/scenario-labs/skills/issues/85)) ([4db8c5f](https://github.com/scenario-labs/skills/commit/4db8c5f3a11969177b1197946c9a222f7d1268b6))
