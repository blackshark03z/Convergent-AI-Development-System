# XP-004 Held-out Oracle

The local oracle tests the frozen outcome through product imports and the real
TimelineBuilder, format validator, saved schedule, Web schedule readback, CLI
render boundary and NvencRenderEngine manifest path. It uses selected local
asset identities and stubs only media normalization/FFmpeg execution; no
provider, GPU or production service is called.

For each F1-F5 format it requires the selected source classes, asset identities,
plan/effect fingerprints, editorial/compose lineage, saved/reloaded schedule,
Web readback, render input list, final manifest and output digest to agree. F3
probes whether changed creative content and a changed selected asset alter
downstream lineage. A tampered F5
schedule with generated media must be rejected before output. The oracle checks
that evaluation leaves candidate files unchanged.

A disposable negative control forces the final manifest to label every output
F2; it must fail on F1. The oracle does not assert a reference patch, class layout,
real encoded video quality, provider behavior or Owner subjective acceptance.
Source media are synthetic local files; the oracle binds their selected paths
and the output digest, while media-content provenance in a live provider run
remains outside this offline qualification.
