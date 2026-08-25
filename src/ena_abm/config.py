from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    """Complete configuration for one simulation run."""

    n_consumers: int = 100
    network_type: str = "small_world"
    mean_degree: int = 6
    rewire_probability: float = 0.10
    strategy: str = "direct"
    market_sociality: float = 0.50
    seed_adopters: int = 3
    fairness_criterion: str = "equal_actions"
    action_budget: int = 40
    budget_limit: float = 40.0
    exposure_quota: int = 40
    direct_action_cost: float = 1.0
    referral_action_cost: float = 1.0
    cost_accounting: str = "upfront_expected"
    direct_exposure_probability: float = 1.0
    referral_acceptance_probability: float = 1.0
    referral_neighbor_availability_probability: float = 1.0
    referral_introduction_probability: float = 1.0
    direct_search_share: float = 0.25
    direct_contact_share: float = 0.25
    direct_coordination_share: float = 0.25
    direct_followup_share: float = 0.25
    referral_identify_share: float = 0.25
    referral_request_share: float = 0.25
    referral_coordination_share: float = 0.25
    referral_followup_share: float = 0.25
    actions_per_tick: int = 2
    horizon: int = 30
    fit_mean: float = 0.60
    fit_sd: float = 0.15
    status_alpha: float = 4.0
    status_beta: float = 3.0
    uncertainty_alpha: float = 3.0
    uncertainty_beta: float = 2.0
    minimum_uncertainty: float = 0.05
    delta_information: float = 0.25
    direct_source_credibility: float = 0.60
    referral_source_credibility: float = 0.60
    beta_0: float = -0.50
    beta_individual: float = 4.00
    beta_social: float = 3.00
    takeoff_share: float = 0.10
    quiet_period: int = 5
    allow_repeated_direct_contact: bool = True
    master_seed: int = 20260724
    replicate_id: int = 0

    def validate(self) -> None:
        if self.n_consumers < 2:
            raise ValueError("n_consumers must be at least 2")
        if self.network_type not in {
            "ring",
            "small_world",
            "preferential_attachment",
            "custom",
        }:
            raise ValueError(f"unsupported network_type: {self.network_type}")
        if self.strategy not in {"direct", "referral"}:
            raise ValueError(f"unsupported strategy: {self.strategy}")
        if self.fairness_criterion not in {
            "equal_actions",
            "equal_budget",
            "equal_exposures",
        }:
            raise ValueError(f"unsupported fairness_criterion: {self.fairness_criterion}")
        if not 0.0 <= self.market_sociality <= 1.0:
            raise ValueError("market_sociality must be in [0, 1]")
        if not 0.0 <= self.rewire_probability <= 1.0:
            raise ValueError("rewire_probability must be in [0, 1]")
        if self.network_type != "custom":
            if self.mean_degree < 2 or self.mean_degree >= self.n_consumers:
                raise ValueError("mean_degree must be >= 2 and < n_consumers")
            if self.mean_degree % 2:
                raise ValueError(
                    "mean_degree must be even for comparable ring/small-world networks"
                )
        if not 0 <= self.seed_adopters < self.n_consumers:
            raise ValueError("seed_adopters must be in [0, n_consumers)")
        if (
            self.action_budget < 0
            or self.budget_limit < 0
            or self.exposure_quota < 0
            or self.actions_per_tick < 1
            or self.horizon < 1
        ):
            raise ValueError("resource limits, capacity, and horizon must be valid")
        if self.direct_action_cost <= 0 or self.referral_action_cost <= 0:
            raise ValueError("action costs must be positive")
        if self.cost_accounting not in {"upfront_expected", "staged"}:
            raise ValueError(
                "cost_accounting must be 'upfront_expected' or 'staged'"
            )
        for name in (
            "fit_mean",
            "minimum_uncertainty",
            "delta_information",
            "direct_source_credibility",
            "referral_source_credibility",
            "takeoff_share",
            "direct_exposure_probability",
            "referral_acceptance_probability",
            "referral_neighbor_availability_probability",
            "referral_introduction_probability",
            "direct_search_share",
            "direct_contact_share",
            "direct_coordination_share",
            "direct_followup_share",
            "referral_identify_share",
            "referral_request_share",
            "referral_coordination_share",
            "referral_followup_share",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        direct_share_sum = (
            self.direct_search_share
            + self.direct_contact_share
            + self.direct_coordination_share
            + self.direct_followup_share
        )
        referral_share_sum = (
            self.referral_identify_share
            + self.referral_request_share
            + self.referral_coordination_share
            + self.referral_followup_share
        )
        if abs(direct_share_sum - 1.0) > 1e-9:
            raise ValueError("direct stage shares must sum to 1")
        if abs(referral_share_sum - 1.0) > 1e-9:
            raise ValueError("referral stage shares must sum to 1")
        if self.fit_sd < 0:
            raise ValueError("fit_sd must be nonnegative")
        for name in ("status_alpha", "status_beta", "uncertainty_alpha", "uncertainty_beta"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.quiet_period < 1:
            raise ValueError("quiet_period must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "ModelConfig":
        allowed = {f.name for f in fields(cls)}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown configuration fields: {sorted(unknown)}")
        config = cls(**values)
        config.validate()
        return config

    def with_updates(self, **changes: Any) -> "ModelConfig":
        config = replace(self, **changes)
        config.validate()
        return config
