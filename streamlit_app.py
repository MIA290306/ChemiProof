"""Streamlit Community Cloud entry point for the ChemiProof research explorer (ADR-021).

On first start it rebuilds the git-ignored dataset and FINAL-PLS-v1 model from the official
Zenodo record and checks they reproduce the locked artifacts (see `chemiproof.deploy`). If any
check fails the explorer still runs, in its documented degraded state (benchmark pages only).
Local use is unchanged: `chemiproof app`.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from chemiproof import deploy
from chemiproof.ui import app
from chemiproof.ui import artifacts as A


@st.cache_resource(show_spinner=False)
def _bootstrap(results: str, data: str, manifest: str) -> deploy.BootstrapReport:
    with st.spinner(
        "First start: downloading the public Zenodo dataset (~96 MB) and rebuilding the locked "
        "research model. This takes a few minutes and happens once per server start."
    ):
        return deploy.ensure_ready(Path(results), Path(data), Path(manifest), Path("data/cache"))


report = _bootstrap(str(A.results_dir()), str(A.data_dir()), str(A.manifest_path()))
if report.status == "failed":
    st.sidebar.warning(
        "Dataset/model rebuild failed, so screening is disabled; published benchmark pages "
        f"still work. Reason: {report.error}"
    )
app.main()
