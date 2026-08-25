from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationAttempt:
    tick: int
    kind: str
    source_id: int | None
    target_id: int | None


@dataclass(frozen=True)
class ExposureEvent:
    tick: int
    kind: str
    source_id: int | None
    target_id: int
    attempt_id: int


@dataclass(frozen=True)
class PendingAdoption:
    consumer_id: int
    probability: float
    utility: float
    social_evidence: float
    social_reliance: float
    individual_evaluation: float
    source_credibility: float | None
    exposure_kind: str | None
    source_id: int | None
    attempt_id: int | None
