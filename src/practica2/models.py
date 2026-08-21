"""Contenedores inmutables para los resultados numéricos de la práctica.

Separar los resultados de la interfaz evita que la lógica matemática dependa de
Streamlit. Esto permite probar cada algoritmo directamente con ``pytest`` y
reutilizar los mismos resultados en la aplicación y en el informe.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EstimateSummary:
    """Estimación Monte Carlo con incertidumbre aproximada del 95 %."""

    estimate: float
    standard_error: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True)
class TruncatedExponentialResult:
    samples: pd.DataFrame
    summary: EstimateSummary
    exact_mean: float
    upper: float


@dataclass(frozen=True)
class CompositionResult:
    samples: pd.DataFrame
    comparison: pd.DataFrame
    weights: np.ndarray
    powers: np.ndarray | None
    case: str


@dataclass(frozen=True)
class InsuranceResult:
    months: pd.DataFrame
    first_month_claims: pd.DataFrame
    summary: EstimateSummary
    exact_probability: float
    expected_aggregate: float


@dataclass(frozen=True)
class NormalRejectionResult:
    samples: pd.DataFrame
    attempts: pd.DataFrame
    mean: float
    variance: float
    acceptance_rate: float
    theoretical_acceptance: float


@dataclass(frozen=True)
class PoissonProcessResult:
    events: pd.DataFrame
    path: pd.DataFrame
    count: int
    expected_count: float
    rate: float
    horizon: float


@dataclass(frozen=True)
class NHPPMethodResult:
    events: pd.DataFrame
    proposals: pd.DataFrame
    count: int
    proposal_count: int
    acceptance_rate: float
    method: str


@dataclass(frozen=True)
class NHPPComparisonResult:
    global_method: NHPPMethodResult
    improved_method: NHPPMethodResult
    expected_count: float
    horizon: float


@dataclass(frozen=True)
class SpatialPoissonResult:
    points: pd.DataFrame
    count: int
    expected_count: float
    count_uniform: float
    rate: float
    radius: float


@dataclass(frozen=True)
class PolarNormalResult:
    pairs: pd.DataFrame
    attempts: pd.DataFrame
    values: np.ndarray
    mean: float
    variance: float
    acceptance_rate: float

