"""Documentation consistency checks (links, milestone graph, Power BI specification, YAML).

These tests protect the plan documents from drifting apart. They run on any platform, need no data
and make no scientific claim.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKIP_DIRS = {
    ".venv",
    ".git",
    "results",
    "data",
    ".claude",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
}
# Files that documents mention as PLANNED but do not exist yet (remove an entry once it is created).
PLANNED_PATHS = {"config/bi/protocol_map.yaml"}


def _md_files() -> list[Path]:
    out = []
    for p in REPO.rglob("*.md"):
        if not (set(p.relative_to(REPO).parts) & SKIP_DIRS):
            out.append(p)
    return sorted(out)


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def test_all_yaml_files_parse():
    files = [p for p in REPO.rglob("*.y*ml") if not (set(p.relative_to(REPO).parts) & SKIP_DIRS)]
    assert files
    for p in files:
        if p.parts[-2:] == ("workflows", "ci.yml") or p.name == ".pre-commit-config.yaml":
            yaml.safe_load(p.read_text(encoding="utf-8"))
        else:
            assert yaml.safe_load(p.read_text(encoding="utf-8")) is not None, p


def test_markdown_links_and_doc_paths_resolve():
    link = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
    code_path = re.compile(r"`((?:docs|config|templates)/[A-Za-z0-9_./-]+\.(?:md|ya?ml))`")
    problems = []
    for f in _md_files():
        text = f.read_text(encoding="utf-8")
        for target in link.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (f.parent / target).resolve().exists():
                problems.append(f"{f.relative_to(REPO)}: link -> {target}")
        for target in code_path.findall(text):
            if "<" in target or "*" in target or target in PLANNED_PATHS:
                continue
            if not (REPO / target).exists():
                problems.append(f"{f.relative_to(REPO)}: path -> {target}")
    assert not problems, "\n".join(problems)


def test_planned_paths_are_really_still_missing():
    for rel in PLANNED_PATHS:
        assert not (REPO / rel).exists(), f"{rel} now exists: remove it from PLANNED_PATHS"


def _milestones():
    data = yaml.safe_load(_read("config/milestones.yaml"))
    return data, {m["id"]: m for m in data["milestones"]}


def test_milestone_graph_is_consistent():
    data, by_id = _milestones()
    ids = [m["id"] for m in data["milestones"]]
    assert ids == ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M6.5", "M7"]
    assert len(set(ids)) == len(ids)
    for m in data["milestones"]:
        assert m["status"] in data["status_enum"]
        for dep in m["prerequisites"] + m.get("soft_prerequisites", []):
            assert dep in by_id, f"{m['id']} depends on unknown {dep}"
            assert ids.index(dep) < ids.index(m["id"]), (
                f"{m['id']} depends on a later milestone {dep}"
            )
    assert by_id["M6.5"]["prerequisites"] == ["M5", "M6"]
    assert by_id["M7"]["prerequisites"] == ["M6"]  # ADR-016: M7 does not depend on M6.5
    assert by_id["M7"]["soft_prerequisites"] == ["M6.5"]
    assert by_id["M6.5"]["kind"] == "optional_extension"


def test_milestone_markdown_and_backlog_match_yaml():
    _, by_id = _milestones()
    milestones_md = _read("docs/project/06_MILESTONES.md")
    for mid in by_id:
        assert re.search(rf"^## {re.escape(mid)} ", milestones_md, re.M), f"heading for {mid}"
    tasks = by_id["M6.5"]["tasks"]
    assert tasks == [f"CP-{n}" for n in range(651, 661)]
    backlog = _read("docs/project/16_TASK_BACKLOG.md")
    for t in tasks:
        assert f"### Task {t}:" in milestones_md, f"task card for {t}"
        assert re.search(rf"^\| {t} \| M6\.5 \|", backlog, re.M), f"backlog row for {t}"
    for t in tasks:  # every card carries the eight required fields
        card = (
            milestones_md.split(f"### Task {t}:")[1].split("### Task ")[0].split("**Exit gate")[0]
        )
        for field in (
            "Objective",
            "Dependencies",
            "Files to create or modify",
            "Technical implementation requirements",
            "Expected deliverables",
            "Acceptance criteria",
            "Verification procedure",
            "Definition of Done",
        ):
            assert f"**{field}:**" in card, f"{t} lacks {field}"


def test_power_bi_appears_consistently_across_documents():
    expectations = {
        "README.md": ["M6.5", "Power BI"],
        "CLAUDE.md": ["Power BI", "M6.5"],
        "AGENTS.md": ["M6.5"],
        "docs/vi/ROADMAP_VI.md": ["M6.5", "Power BI"],
        "docs/vi/START_HERE_VI.md": ["Power BI"],
        "docs/00_DOCS_INDEX.md": [
            "18_POWER_BI_SPEC.md",
            "19_POWER_BI_DATA_MODEL.md",
            "20_POWER_BI_ACCEPTANCE_TESTS.md",
        ],
        "docs/product/01_PRD.md": ["F-15", "Power BI"],
        "docs/product/08_UX_SPEC.md": ["Power BI"],
        "docs/engineering/04_ARCHITECTURE.md": ["Power BI", "BI export layer"],
        "docs/engineering/07_ACCEPTANCE_TESTS.md": ["BI001", "BI020"],
        "docs/engineering/11_DEV_SETUP.md": ["Power BI", "macOS"],
        "docs/engineering/12_AI_PROMPTS.md": ["PROMPT 6.5"],
        "docs/science/05_EVALUATION_PLAN.md": ["BI", "protocol id"],
        "docs/science/09_RISK_REGISTER.md": ["R21", "R27"],
        "docs/science/10_REFERENCES_AND_LICENSES.md": ["Power BI"],
        "docs/project/06_MILESTONES.md": ["M6.5"],
        "docs/project/13_DECISION_LOG.md": ["ADR-016"],
        "docs/project/14_PROGRESS_LOG.md": ["M6.5"],
        "docs/project/16_TASK_BACKLOG.md": ["CP-651", "CP-660"],
    }
    for rel, needles in expectations.items():
        text = _read(rel)
        for n in needles:
            assert n in text, f"{rel} lacks {n!r}"


def test_power_bi_documents_state_that_nothing_is_built():
    assert "SPECIFICATION ONLY" in _read("docs/bi/18_POWER_BI_SPEC.md")
    assert "SPECIFICATION ONLY" in _read("docs/bi/19_POWER_BI_DATA_MODEL.md")
    assert "NO TEST HAS BEEN WRITTEN OR RUN" in _read("docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md")
    built = [
        p
        for p in REPO.rglob("*")
        if p.suffix in {".pbix", ".pbip", ".pbit"}
        and not (set(p.relative_to(REPO).parts) & SKIP_DIRS)
    ]
    _, by_id = _milestones()
    if built:  # a Power BI file may exist only once M6.5 has left NOT_STARTED
        assert by_id["M6.5"]["status"] != "NOT_STARTED", built
    else:
        assert by_id["M6.5"]["status"] in {"NOT_STARTED", "BLOCKED"}


CONTRACT = "config/bi/export_contract.yaml"


def _doc19_tables() -> dict[str, list[str]]:
    text = _read("docs/bi/19_POWER_BI_DATA_MODEL.md")
    out: dict[str, list[str]] = {}
    for name, body in re.findall(r"^### `([a-z_]+)`\n(.*?)(?=^### |^## )", text, re.M | re.S):
        out[name] = re.findall(r"^\| `([a-z_0-9]+)` \|", body, re.M)
    return out


def test_data_contract_yaml_matches_the_markdown_tables():
    contract = yaml.safe_load(_read(CONTRACT))
    assert contract["contract_version"] == "bi-contract-1.0.0"
    assert contract["status"] == "SPECIFIED_NOT_IMPLEMENTED"
    doc_tables = _doc19_tables()
    assert set(doc_tables) == set(contract["tables"])
    expected = {
        "dim_sample",
        "dim_adulterant",
        "dim_experiment",
        "fact_predictions",
        "fact_model_metrics",
        "fact_uncertainty",
        "fact_data_quality",
    }
    assert expected <= set(contract["tables"])  # the suggested starting tables are all present
    for name, spec in contract["tables"].items():
        cols = [c["name"] for c in spec["columns"]]
        assert cols == doc_tables[name], f"column mismatch in {name}"
        assert len(cols) == len(set(cols))
        assert set(spec["primary_key"]) <= set(cols)
        for c in spec["columns"]:
            assert c["type"] in {"string", "int", "decimal", "bool", "datetime"}, (name, c)
    # relationships: endpoints exist and the count matches the document
    for rel in contract["relationships"]:
        for end in (rel["one"], rel["many"]):
            table, col = re.match(r"(\w+)\[(\w+)\]", end).groups()
            assert col in [c["name"] for c in contract["tables"][table]["columns"]], end
    rows = re.findall(
        r"^\| `(?:dim|fact)_\w+\[\w+\]` \| `(?:dim|fact)_\w+\[\w+\]` \|",
        _read("docs/bi/19_POWER_BI_DATA_MODEL.md"),
        re.M,
    )
    assert len(rows) == len(contract["relationships"]) == 22


def test_contract_enforces_provenance_units_and_separation():
    contract = yaml.safe_load(_read(CONTRACT))
    t = contract["tables"]
    for fact in (
        "fact_predictions",
        "fact_model_metrics",
        "fact_uncertainty",
        "fact_selective_risk",
        "fact_ot_diagnostics",
        "fact_robustness",
    ):
        cols = {c["name"] for c in t[fact]["columns"]}
        assert {"run_id", "model_key", "mode"} <= cols, fact  # identity on every fact
    exp = {c["name"] for c in t["dim_experiment"]["columns"]}
    assert {
        "protocol_id",
        "run_class",
        "config_sha256",
        "manifest_sha256",
        "git_head",
        "git_dirty",
        "is_headline",
        "label_convention",
    } <= exp
    unc = {c["name"] for c in t["fact_uncertainty"]["columns"]}
    assert {
        "interval_method",
        "interval_nominal_level",
        "calibration_protocol",
        "threshold_fit_source",
        "covered",
    } <= unc
    pp = [c for c in t["fact_model_metrics"]["columns"] if c["name"] == "mae_pp"][0]
    assert pp["unit"] == "percentage points"
    ref = {c["name"] for c in t["fact_published_reference"]["columns"]}
    assert "is_measured" in ref
    related = {r["many"].split("[")[0] for r in contract["relationships"]}
    assert "fact_published_reference" not in related and "fact_data_issues" not in related


def test_bi_acceptance_test_ids_are_complete_unique_and_referenced():
    text = _read("docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md")
    ids = re.findall(r"^\| (BI\d{3}) \|", text, re.M)
    assert ids == [f"BI{n:03d}" for n in list(range(1, 15)) + list(range(20, 33))]
    assert len(set(ids)) == len(ids)
    assert "NOT RUN" in text
    rows = [ln for ln in text.splitlines() if re.match(r"^\| BI\d{3} \|", ln)]
    for ln in rows:  # status is the last cell; only these values are allowed
        assert ln.rstrip().split("|")[-2].strip() in {"NOT RUN", "PASS", "FAIL", "BLOCKED"}, ln
    for rule in ("V-01", "V-12"):
        assert rule in _read("docs/bi/19_POWER_BI_DATA_MODEL.md")
    assert "docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md" in _read(
        "docs/engineering/07_ACCEPTANCE_TESTS.md"
    )


def test_dashboard_name_and_four_pages_are_specified():
    spec = _read("docs/bi/18_POWER_BI_SPEC.md")
    assert "ChemiProof: Food Authenticity & Quality Intelligence" in spec
    for page in (
        "Page 1: Dataset & Quality Overview",
        "Page 2: Machine Learning Performance",
        "Page 3: Uncertainty & Screening Assessment",
        "Page 4: Scientific Research Insights",
    ):
        assert page in spec
    for rule in (
        "No leakage",
        "Protocol identity",
        "Transductive is labeled",
        "No invented thresholds",
    ):
        assert rule in spec


@pytest.mark.parametrize(
    "forbidden",
    [
        "a native .pbix was built",
        "dashboard has been built",
        "dashboard is validated",
        "validated dashboard",
    ],
)
def test_no_document_claims_the_dashboard_exists(forbidden):
    for f in _md_files():
        rel = f.relative_to(REPO).as_posix()
        if rel.startswith(("results/",)):
            continue
        assert forbidden not in f.read_text(encoding="utf-8").lower(), (rel, forbidden)
