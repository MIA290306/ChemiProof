"""ChemiProof research explorer (M6). Research screening only; not a certified authenticity test.

Run from the repository root: `chemiproof app` (or `streamlit run src/chemiproof/ui/app.py`).
Benchmark pages copy numbers from validated run folders. The only computations are the ones
ADR-018 declares on the user's own files: FINAL-PLS-v1 (single file) and batch OT (opt-in).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chemiproof import pipeline
from chemiproof.data.parser import parse_dat_bytes
from chemiproof.errors import ChemiProofError
from chemiproof.modeling.final import latest_artifact, load_final
from chemiproof.modeling.ot import MIN_TARGET_BATCH, TRANSDUCTIVE_WARNING
from chemiproof.spectra.preprocess import AUTHOR_V1, preprocess_intensity
from chemiproof.ui import artifacts as A

DISCLAIMER = (
    "Research prototype: experimental estimates of olive-oil volume fraction from EEM "
    "fluorescence spectra. Not a certified authenticity test; no regulatory or safety meaning."
)
BATCH_NOTE = (
    "Research transductive mode: this procedure adapts using the unlabeled spectra of the full "
    "batch."
)
COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]  # Okabe-Ito
INTENSITY_UNIT = "Counts/uA (instrument unit as reported in the file header)"


@st.cache_resource
def _model(path: str):
    return load_final(Path(path))


@st.cache_resource
def _dataset(manifest: str, data: str):
    return pipeline.load_dataset(Path(manifest), Path(data))


@st.cache_data
def _csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def current_model():
    art = latest_artifact(A.results_dir())
    if art is None:
        return None
    try:
        return _model(str(art))
    except ChemiProofError as err:
        st.error(A.user_message(err))
        return None


def dataset_or_none():
    try:
        return _dataset(str(A.manifest_path()), str(A.data_dir()))
    except ChemiProofError:
        return None


def chart_table(df: pd.DataFrame, caption: str) -> None:
    """Accessible alternative for every chart: the plotted numbers as a table."""
    with st.expander(f"Data table: {caption}"):
        st.dataframe(df, hide_index=True)


def heatmap(spec, processed: bool) -> go.Figure:
    z = preprocess_intensity(spec.intensity) if processed else spec.intensity
    unit = "unitless (author_v1, max-normalised)" if processed else INTENSITY_UNIT
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=spec.emission_nm,
            y=spec.excitation_nm,
            colorscale="Viridis",
            colorbar={"title": {"text": unit, "side": "right"}},
        )
    )
    fig.update_layout(
        xaxis_title="Emission wavelength (nm)",
        yaxis_title="Excitation (nm)",
        height=420,
        margin={"t": 30},
    )
    return fig


def validation_strip(spec, warnings: list[str]) -> None:
    cols = st.columns(4)
    cols[0].markdown("Parser ✓")
    cols[1].markdown(f"Grid ✓ {spec.excitation_nm.size}×{spec.emission_nm.size}")
    cols[2].markdown("Finite values ✓")
    neg = int(np.sum(spec.intensity < 0))
    cols[3].markdown(f"Negative cells {'!' if neg else '✓'} ({neg})")
    for w in warnings:
        st.caption(f"⚠ {w}")


def page_overview() -> None:
    st.title("ChemiProof / Spectral Screening Research")
    st.markdown(
        "Experimental estimates of olive-oil volume fraction from EEM fluorescence spectra."
    )
    st.info(DISCLAIMER)
    runs = A.benchmark_runs(A.results_dir())
    if not runs:
        st.warning("No verified benchmark results yet.")
        return
    st.markdown(
        ":blue-badge[Inductive (no target batch)] "
        ":orange-badge[Transductive (unlabeled target batch used)]"
    )
    st.caption(
        f"Last locked run: {max(r.utc_time for r in runs)}. Milestones M0-M5: review required; "
        "M6 explorer: in progress."
    )
    st.subheader("Our measured results (LOAO: each adulterant held out in turn)")
    rows = pd.DataFrame(A.headline_rows(runs))
    st.dataframe(rows, hide_index=True)
    st.caption(
        "MAE in percentage points of olive-oil volume fraction (1 pp = 0.01 fraction); macro = "
        "unweighted mean over the five held-out adulterants. Group sizes 60/60/90/90/30 and EVOO "
        "brands are imbalanced (walnut: one brand). Transductive rows needed the whole unlabeled "
        "held-out batch and are not single-file performance."
    )
    ref = A.published_reference(runs)
    if ref:
        st.subheader("Published reference (not a ChemiProof measurement)")
        st.dataframe(
            pd.DataFrame([{k: v for k, v in ref.items() if k not in ("caveat",)}]), hide_index=True
        )
        st.caption(f"Source: {ref['source']}. {ref['caveat']}")


def page_explore() -> None:
    st.header("Explore EEM")
    ds = dataset_or_none()
    options = ["Upload a .dat file"] + (["Audited dataset sample"] if ds else [])
    src = st.radio("Spectrum source", options, horizontal=True)
    spec, warnings, meta = None, [], {}
    if src == "Audited dataset sample" and ds:
        ids = [r.sample_id for r in ds.rows]
        sid = st.selectbox("Sample", ids)
        i = ids.index(sid)
        spec, row = ds.spectra[i], ds.rows[i]
        meta = {
            "sample_id": row.sample_id,
            "adulterant": row.adulterant_type,
            "brand": row.evoo_brand,
            "olive_fraction": round(row.olive_fraction, 4),
            "ratio_folder": row.olive_ratio_raw,
            "round": row.measurement_round,
            "sha256": row.sha256,
            "qc": f"{row.qc_status} {row.qc_flags}",
        }
    else:
        up = st.file_uploader("EEM .dat file (Zenodo 19755088 layout)", type=["dat"])
        if up is None:
            st.caption(
                "No file selected." + ("" if ds else " Audited dataset not on this machine.")
            )
            return
        try:
            spec = parse_dat_bytes(up.getvalue(), up.name).spectrum
        except ChemiProofError as err:
            st.error(A.user_message(err))
            return
        meta = {"file": up.name}
    if spec.intensity.min() < 0:
        warnings.append("NEGATIVE_INTENSITY: negative cells kept as measured (never clamped)")
    validation_strip(spec, warnings)
    st.json(meta, expanded=False)
    processed = st.toggle("Show preprocessed (author_v1)", value=False)
    st.plotly_chart(heatmap(spec, processed), use_container_width=True)
    st.caption("Preprocessing author_v1: " + "; ".join(AUTHOR_V1.describe()))
    z = preprocess_intensity(spec.intensity) if processed else spec.intensity
    ex = st.select_slider("Excitation slice (nm)", options=[float(x) for x in spec.excitation_nm])
    j = int(np.where(spec.excitation_nm == ex)[0][0])
    fig = go.Figure(go.Scatter(x=spec.emission_nm, y=z[j], line={"color": COLORS[0]}))
    fig.update_layout(
        xaxis_title="Emission wavelength (nm)",
        height=300,
        margin={"t": 20},
        yaxis_title="unitless" if processed else "Counts/uA",
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_table(
        pd.DataFrame({"emission_nm": spec.emission_nm, "intensity": z[j]}),
        f"emission spectrum at excitation {ex:g} nm",
    )


def _fold_plot(pred: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for k, (model, g) in enumerate(pred.groupby("model")):
        fig.add_scatter(
            x=g["y_true_fraction"],
            y=g["y_pred_fraction"],
            mode="markers",
            name=model,
            marker={"color": COLORS[k % len(COLORS)], "size": 7},
        )
    fig.add_scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="y = x", line={"color": "#888", "dash": "dot"}
    )
    fig.update_layout(
        xaxis_title="Actual olive fraction",
        yaxis_title="Estimated olive fraction",
        height=420,
        margin={"t": 20},
    )
    return fig


def page_benchmarks() -> None:
    st.header("Benchmarks")
    runs = A.benchmark_runs(A.results_dir())
    loao = [r for r in runs if r.protocol == "loao"]
    if not loao:
        st.warning("No verified benchmark results yet.")
        return
    run = st.selectbox("Run", loao, format_func=lambda r: r.label)
    summary = A.read_json(run.path / "summary.json")
    if summary.get("mode") == "transductive_batch":
        st.warning(summary.get("transductive_warning", TRANSDUCTIVE_WARNING))
    metrics = _csv(str(run.path / "metrics_by_fold.csv"))
    pred = _csv(str(run.path / "predictions.csv"))
    fold = st.selectbox("Held-out adulterant (outer fold)", sorted(metrics["fold_id"].unique()))
    m = metrics[metrics["fold_id"] == fold].copy()
    m["mode"] = m["mode"].map(lambda x: A.MODE_LABEL.get(x, x))
    p = pred[pred["fold_id"] == fold]
    brands = p.drop_duplicates("sample_id")["sample_id"].map(A.brand_of).value_counts()
    st.markdown(
        f"**n = {int(m['n'].iloc[0])}** held-out spectra · brands: "
        + ", ".join(f"{b} {n}" for b, n in brands.items())
        + f" · protocol `{run.protocol}` · run `{run.run_id}`"
    )
    cols = ["model", "mode", "n", "mae_pp", "rmse_fraction", "bias_fraction", "r2"]
    st.dataframe(m[cols].round(4), hide_index=True)
    st.caption("MAE in percentage points; RMSE and bias in fraction units; scoring unclipped.")
    worst = metrics.loc[metrics.groupby("model")["mae_pp"].idxmax(), ["model", "fold_id", "mae_pp"]]
    st.caption(
        "Worst fold per model: "
        + "; ".join(f"{r.model} {r.fold_id} {r.mae_pp:.2f} pp" for r in worst.itertuples())
    )
    models = st.multiselect(
        "Models in the plot", sorted(p["model"].unique()), default=sorted(p["model"].unique())[:2]
    )
    q = p[p["model"].isin(models)]
    st.plotly_chart(_fold_plot(q), use_container_width=True)
    chart_table(
        q[["sample_id", "model", "y_true_fraction", "y_pred_fraction"]], "estimated vs actual"
    )
    _uq_section(runs)


def _uq_section(runs: list[A.Run]) -> None:
    uq = [r for r in runs if r.protocol == "LOAO-UQ-v1"]
    if not uq:
        return
    run = uq[0]
    st.subheader("Abstention and intervals (LOAO-UQ-v1, inductive)")
    st.caption(
        "Label-free risk score; thresholds fitted on source adulterants only. "
        "Empirical coverage; no guarantee under a new adulterant."
    )
    curve = _csv(str(run.path / "risk_coverage_curve.csv"))
    c1, c2, c3 = st.columns(3)
    model = c1.selectbox("Model", sorted(curve["model"].unique()), key="uq_model")
    score = c2.selectbox("Risk score", sorted(curve["score"].unique()), key="uq_score")
    fold = c3.selectbox("Fold", sorted(curve["fold_id"].unique()), key="uq_fold")
    g = curve[(curve.model == model) & (curve.score == score) & (curve.fold_id == fold)]
    g = g.sort_values("retention_percent")
    fig = go.Figure()
    fig.add_scatter(
        x=g.retention_percent,
        y=100 * g.random_p95,
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=g.retention_percent,
        y=100 * g.random_p05,
        fill="tonexty",
        fillcolor="rgba(136,136,136,0.25)",
        line={"width": 0},
        name="random rejection 5-95 %",
    )
    fig.add_scatter(
        x=g.retention_percent,
        y=100 * g.rank_selective_mae,
        name=f"{score} ranking",
        line={"color": COLORS[0]},
    )
    fig.update_layout(
        xaxis_title="Retained spectra (%)",
        yaxis_title="MAE of retained (pp)",
        xaxis_autorange="reversed",
        height=380,
        margin={"t": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_table(
        g[["retention_percent", "rank_selective_mae", "random_p05", "random_p95"]],
        "selective risk vs retention (fraction units)",
    )
    verdicts = A.read_json(run.path / "usefulness.json")["verdicts"]
    v = verdicts.get(f"{model}/{score}")
    if v:
        verdict = "met" if v["useful_on_this_benchmark"] else "NOT met"
        st.markdown(
            f"Preregistered usefulness rule: **{verdict}** "
            f"({v['folds_threshold_improved']}/5 folds improved, "
            f"{v['folds_beat_random_p05']}/5 beat random 5th percentile)."
        )
    cov = _csv(str(run.path / "interval_coverage.csv"))
    st.dataframe(
        cov[(cov.model == model)][
            ["fold_id", "variant", "nominal_level", "observed_coverage", "mean_width_fraction", "n"]
        ].round(3),
        hide_index=True,
    )
    fails = _csv(str(run.path / "failure_cases.csv"))
    st.markdown("**Largest errors (failure cases)**")
    st.dataframe(fails[fails.model == model].head(10).round(3), hide_index=True)


def page_screen() -> None:
    st.header("Screen sample (inductive, single file)")
    model = current_model()
    if model is None:
        st.warning(A.MESSAGES[A.StatusCode.NO_TRAINED_MODEL])
        return
    card = model.card
    st.caption(
        f"Model {card['protocol_id']} ({card['model']}, {card['n_components']} components), "
        f"mode {A.MODE_LABEL[card['mode']]}, run {card.get('run_id')}. "
        "Studied matrix: EVOO binary blends with soybean, peanut, rapeseed, corn or "
        "walnut oil."
    )
    up = st.file_uploader("EEM .dat file", type=["dat"], key="screen_upload")
    if up is None:
        return
    try:
        res = pipeline.screen_single(up.getvalue(), up.name, model)
    except ChemiProofError as err:
        st.error("No estimate: validation failed. " + A.user_message(err))
        return
    validation_strip(res.spectrum, res.warnings)
    if res.olive_fraction is None:
        st.warning(
            "Review required — estimate withheld. Reason: model risk. "
            + A.MESSAGES[A.StatusCode.ABSTAIN_OOD_RISK]
        )
    else:
        f = res.olive_fraction
        st.subheader(f"Estimated olive-oil fraction: {f:.2f} ({100 * f:.0f}%)")
        lo, hi = res.interval["pooled"]
        st.markdown(
            f"Empirical research interval (nominal 90 %): {lo:.2f} to {hi:.2f} fraction. "
            "Empirical research interval; coverage on unseen adulterants is not "
            "guaranteed."
        )
        st.caption(f"Adulterant fraction (binary mixtures only) = 1 - {f:.2f} = {1 - f:.2f}.")
    st.caption(
        f"OOD score {res.ood_score:.2f} (review threshold {res.ood_threshold:.2f}); "
        "a weak research-level cue, not a validated detector."
    )
    st.plotly_chart(heatmap(res.spectrum, processed=False), use_container_width=True)
    with st.expander("Limitations"):
        for x in card["limitations"]:
            st.markdown(f"- {x}")
    st.download_button(
        "Download screening report (Markdown)",
        A.screening_report_md(res, card),
        file_name=f"chemiproof_screening_{res.file_sha256[:12]}.md",
    )


def page_batch() -> None:
    st.header("Batch research (transductive OT)")
    st.warning(BATCH_NOTE + " " + TRANSDUCTIVE_WARNING)
    st.markdown(
        f"- Needs at least {MIN_TARGET_BATCH} spectra; separate from single-sample screening.\n"
        "- Source = all 330 labelled spectra; this exact configuration was never evaluated.\n"
        "- Batches whose olive levels are skewed made OT fail badly in M4 stress tests "
        "(R2 about -3)."
    )
    model, ds = current_model(), dataset_or_none()
    if model is None:
        st.warning(A.MESSAGES[A.StatusCode.NO_TRAINED_MODEL])
        return
    if ds is None:
        st.warning(A.MESSAGES[A.StatusCode.DATASET_NOT_AVAILABLE])
        return
    ups = st.file_uploader("Batch of EEM .dat files", type=["dat"], accept_multiple_files=True)
    agree = st.checkbox("I understand this is a transductive research analysis of this batch only.")
    if not st.button("Run batch analysis", disabled=not (ups and agree)):
        return
    try:
        res = pipeline.screen_batch([(u.name, u.getvalue()) for u in ups], ds, model)
    except ChemiProofError as err:
        st.error(A.user_message(err))
        return
    st.markdown(
        f"Batch manifest ID `{res.batch_sha256[:16]}` · {len(res.sample_ids)} spectra · "
        f"Sinkhorn converged: {res.diagnostics['converged']} "
        f"({res.diagnostics['n_iter']} iterations)"
    )
    out = pd.DataFrame(
        {"file": res.sample_ids, "olive_fraction (transductive)": res.olive_fraction}
    )
    st.dataframe(out.round(3), hide_index=True)
    st.json(res.diagnostics, expanded=False)


def page_methods() -> None:
    st.header("Methods & provenance")
    model = current_model()
    card = model.card if model else None
    st.markdown(
        "- Data: Zenodo [10.5281/zenodo.19755088](https://doi.org/10.5281/zenodo.19755088), "
        "CC BY 4.0; raw files are never redistributed.\n"
        "- Paper: Sun et al. 2026, npj Science of Food, "
        "[10.1038/s41538-026-01037-6](https://doi.org/10.1038/s41538-026-01037-6).\n"
        "- Label: olive-oil volume fraction = a / (a + b) for folder ratio a:b (ADR-008).\n"
        "- Splits: five leave-one-adulterant-out folds; inner model selection on source only.\n"
        "- Preprocessing author_v1: " + "; ".join(AUTHOR_V1.describe()) + "\n"
        "- Calibration caveat: intervals and thresholds use source adulterants only; observed "
        "coverage on a new adulterant is empirical, never guaranteed."
    )
    if card:
        st.subheader("Screening model card")
        st.json({k: v for k, v in card.items() if k != "limitations"}, expanded=False)
    else:
        st.info(A.MESSAGES[A.StatusCode.NO_TRAINED_MODEL])
    runs = A.benchmark_runs(A.results_dir())
    st.download_button(
        "Export reproducibility report (Markdown)",
        A.methods_report_md(card, runs),
        file_name="chemiproof_reproducibility.md",
    )
    if card:
        st.download_button(
            "Download model card (JSON)", json.dumps(card, indent=2), file_name="model_card.json"
        )


PAGES = {
    "Overview": page_overview,
    "Explore EEM": page_explore,
    "Benchmarks": page_benchmarks,
    "Screen sample": page_screen,
    "Batch research": page_batch,
    "Methods & provenance": page_methods,
}


def main() -> None:
    st.set_page_config(page_title="ChemiProof research explorer", layout="wide")
    page = st.sidebar.radio("Section", list(PAGES))
    st.sidebar.caption(DISCLAIMER)
    PAGES[page]()


main()
