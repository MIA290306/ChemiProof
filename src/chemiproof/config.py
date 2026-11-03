"""Config loading and validation. Runs before any training or evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from chemiproof.errors import ChemiProofError, StatusCode

ADULTERANTS = ("soybean", "peanut", "rapeseed", "corn", "walnut")


class ProjectInfo(BaseModel):
    name: str
    owner: str
    stage: str
    default_seed: int
    primary_target: Literal["olive_oil_volume_fraction"]
    target_unit: Literal["fraction"]
    accepted_range: tuple[float, float]

    @field_validator("accepted_range")
    @classmethod
    def _unit_interval(cls, v: tuple[float, float]) -> tuple[float, float]:
        if v != (0.0, 1.0):
            raise ValueError("accepted_range must be [0, 1] (olive volume fraction)")
        return v


class SpectraInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    excitation_channels: int
    emission_channels: int
    expected_features: int

    @model_validator(mode="after")
    def _features_match(self) -> SpectraInfo:
        if self.excitation_channels * self.emission_channels != self.expected_features:
            raise ValueError("expected_features must equal excitation_channels * emission_channels")
        return self


class EvaluationInfo(BaseModel):
    outer_split: Literal["leave_one_adulterant_out"]
    adversarial_label_access: Literal["disallow"]
    adulterants: list[str]
    report_macro_and_pooled: Literal[True]

    @field_validator("adulterants")
    @classmethod
    def _five_known(cls, v: list[str]) -> list[str]:
        if sorted(v) != sorted(ADULTERANTS):
            raise ValueError(f"adulterants must be exactly {list(ADULTERANTS)}")
        return v


class UiInfo(BaseModel):
    certified_authenticity_claims: Literal[False]
    allow_inductive_single_sample: bool
    allow_transductive_single_sample: Literal[False]


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    project: ProjectInfo
    source: dict[str, Any]
    spectra: SpectraInfo
    evaluation: EvaluationInfo
    ui: UiInfo


class ExperimentConfig(BaseModel):
    """Sections not yet specified (preprocessing, models, ...) are kept as-is (extra='allow')."""

    model_config = ConfigDict(extra="allow")
    experiment_id: str
    status: Literal["NOT_RUN"]  # only real runs may change this, never a hand edit
    random_seed: int
    mode: Literal["inductive", "transductive_batch"]
    protocol: Literal["source_internal_loro", "loao"] = "loao"
    run_class: Literal["exploratory", "locked"] = "exploratory"
    subset_brand: Literal["luhua", "olivera", "earl_grey"] | None = None
    outer_cv: Literal["leave_one_adulterant_out"] | None = None
    models: (
        list[
            Literal[
                "mean_y",
                "svr_raw",
                "pca_svr",
                "pls",
                "ot_svr",
                "ot_svr_pot",
                "author_pca50",
                "author_pca10",
                "svr_no_adaptation",
            ]
        ]
        | None
    ) = None
    metrics: list[Literal["mae", "rmse", "bias", "r2"]]
    allowed_target_information: Literal["unlabeled_X_only"] | None = None
    forbidden_target_information: list[str] = []
    label_unit: Literal["fraction"] | None = None

    @model_validator(mode="after")
    def _mode_rules(self) -> ExperimentConfig:
        inductive_keys = {"mean_y", "svr_raw", "pca_svr", "pls"}
        transductive_keys = {
            "ot_svr",
            "ot_svr_pot",
            "author_pca50",
            "author_pca10",
            "svr_no_adaptation",
        }
        if self.models is not None:
            allowed = inductive_keys if self.mode == "inductive" else transductive_keys
            bad = set(self.models) - allowed
            if bad:
                raise ValueError(f"models {sorted(bad)} are not valid for mode {self.mode!r}")
        if self.protocol == "loao" and self.outer_cv is None:
            raise ValueError("protocol 'loao' requires outer_cv: leave_one_adulterant_out")
        if self.mode == "transductive_batch":
            if self.allowed_target_information != "unlabeled_X_only":
                raise ValueError(
                    "transductive_batch requires allowed_target_information: unlabeled_X_only"
                )
            if "y" not in self.forbidden_target_information:
                raise ValueError("transductive_batch must list 'y' in forbidden_target_information")
        elif self.allowed_target_information is not None:
            raise ValueError("inductive mode must not declare target information access")
        return self


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "config file not found", path=path.name)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))  # safe_load only, never load()
    except yaml.YAMLError as exc:
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, "YAML parse error", path=path.name
        ) from exc
    if not isinstance(data, dict):
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, "config root must be a mapping", path=path.name
        )
    return data


def _validate[T: BaseModel](model: type[T], data: dict[str, Any], path: Path) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        raise ChemiProofError(StatusCode.INVALID_CONFIG, problems, path=path.name) from exc


def load_project_config(path: Path) -> ProjectConfig:
    return _validate(ProjectConfig, _load_yaml(path), path)


def load_experiment_config(path: Path) -> ExperimentConfig:
    return _validate(ExperimentConfig, _load_yaml(path), path)
