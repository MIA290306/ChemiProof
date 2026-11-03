# AGENTS.md

AI coding agents (Claude Code, Codex, Cursor, Copilot) must first read [`CLAUDE.md`](CLAUDE.md) and the numbered docs. This is a **scientific research project**, not a generic AI SaaS dashboard.

**Current state:** milestones M0-M4 are implemented and awaiting owner review (see `docs/project/14_PROGRESS_LOG.md`); work on the first incomplete milestone only. Milestone M6.5 (Power BI quality-analytics layer, optional extension, Windows-only tool) is specified in `docs/bi/` but not started. Never state experimental performance absent generated artifacts. Do not modify evaluation protocol to inflate metrics. Uphold the train/validation/calibration/test separation. Preserve honest labels for batch-transductive versus single-sample-inductive use.

Before every phase: plan → implement → test → document artifacts → milestone handoff → wait for owner review. For detailed completion gates see `docs/engineering/07_ACCEPTANCE_TESTS.md`.

BI layer (M6.5): Power BI only presents exported, validated results. Python computes all metrics; never mix protocols or modes in a BI view; never claim a dashboard is built or validated without the evidence defined in `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`.
