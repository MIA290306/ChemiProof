# Documentation map and dependencies

Numbers (`01`–`17`) are stable document IDs used in prompts and task reviews ("the docs numbered 02, 05"). Folders group them by purpose.

```text
README.md  CLAUDE.md  AGENTS.md      <- repo root (tools look for these here)
docs/
  00_DOCS_INDEX.md                   <- this file
  product/      what we build and for whom        (01, 08)
  science/      protocol, data, evaluation, risk  (02, 03, 05, 09, 10)
  engineering/  how we build and verify it        (04, 07, 11, 12)
  project/      plan, decisions, progress, release (06, 13, 14, 15, 16)
  release/      M7 drafts: research report, model card, data card, release review
  bi/           Power BI quality-analytics layer, milestone M6.5 (18, 19, 20) - specification only
  vi/           Vietnamese onboarding for the owner (START_HERE, ROADMAP, 17)
templates/      MILESTONE_REVIEW.md, RESEARCH_REPORT.md
config/         project.yaml, milestones.yaml, experiments/, bi/export_contract.yaml
```

## Product — `docs/product/`

| Document | Main question | Reader |
|---|---|---|
| `01_PRD.md` | What is ChemiProof and what is in/out of scope? | Owner + developer |
| `08_UX_SPEC.md` | Which screens and words should users see? | UI engineer |

## Science — `docs/science/`

| Document | Main question | Reader |
|---|---|---|
| `02_RESEARCH_PROTOCOL.md` | Which research questions, hypotheses and methods? | Research lead + model dev |
| `03_DATA_CONTRACT.md` | What exact data must be validated? | Data engineer |
| `05_EVALUATION_PLAN.md` | How is success measured without leakage? | ML researcher |
| `09_RISK_REGISTER.md` | What can invalidate or mislead the study? | All |
| `10_REFERENCES_AND_LICENSES.md` | Which published sources and rights need review? | All |

## Engineering — `docs/engineering/`

| Document | Main question | Reader |
|---|---|---|
| `04_ARCHITECTURE.md` | How are components and APIs organized? | Engineer |
| `07_ACCEPTANCE_TESTS.md` | How can the owner verify work really passed? | QA + owner |
| `11_DEV_SETUP.md` | How should the coding environment be configured? | Developer |
| `12_AI_PROMPTS.md` | What exact prompt should be sent to an agent? | Owner |

## Project management — `docs/project/`

| Document | Main question | Reader |
|---|---|---|
| `06_MILESTONES.md` | What ships at each gate? | Agent + owner |
| `13_DECISION_LOG.md` | Why were scientific/technical choices made? | All |
| `14_PROGRESS_LOG.md` | Which gates have evidence of completion? | All |
| `15_RELEASE_AND_RESEARCH_REPORT.md` | What must be presented before public release? | Owner |
| `16_TASK_BACKLOG.md` | What exact task should the agent implement next? | Agent |

## Release drafts — `docs/release/` (M7, REVIEW REQUIRED)

| Document | Main question | Reader |
|---|---|---|
| `RESEARCH_REPORT.md` | What did ChemiProof measure, and what does it not show? | Reviewer, public |
| `MODEL_CARD.md` | What is FINAL-PLS-v1, how good is the evidence, what must it not be used for? | User, reviewer |
| `DATA_CARD.md` | What is in the dataset we used, and how reliable is it? | Reviewer |
| `RELEASE_REVIEW.md` | Are rights, citations and reproduction cleared; what blocks the tag? | Owner, external reviewer |

## Power BI layer (M6.5, specification only) — `docs/bi/`

| Document | Main question | Reader |
|---|---|---|
| `18_POWER_BI_SPEC.md` | What is the dashboard, which rules bind it, and what are its environment limits? | Owner + BI engineer |
| `19_POWER_BI_DATA_MODEL.md` | Which tables, columns, units, relationships, KPIs and validation rules does the export need? | Data engineer + BI engineer |
| `20_POWER_BI_ACCEPTANCE_TESTS.md` | How do we prove the export and the dashboard are correct (and when is M6.5 done)? | QA + owner |

## Delivery policy

- **No phase skipping.** UI work begins after validated model/evaluation infrastructure exists.
- Project repo contains **your code**, not copies of upstream code unless rights review permits it.
- Artifacts in `results/` must contain reproducible run IDs, config fingerprints, environment info, data manifest hash, numeric per-fold tables and report generation command.
- Status language: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `REVIEW REQUIRED`, `ACCEPTED`. No ambiguous “done”.

## Science vocabulary

- EEM: excitation–emission matrix (fluorescence intensities over wavelength axes)
- y: olive-oil **volume** fraction, not mass fraction, not probability of being authentic
- LOAO: leave-one-adulterant-out, an entire oil system is held out
- Inductive: predictions without adapting to the held-out target batch
- Transductive: adaptation uses unlabeled target feature vectors as a batch
- Selective risk: prediction error among non-abstained cases at a specified acceptance/coverage fraction

## Starting point

Owner reads `README.md`; coding agent reads `CLAUDE.md`; then begin M0 in `docs/project/06_MILESTONES.md`.
