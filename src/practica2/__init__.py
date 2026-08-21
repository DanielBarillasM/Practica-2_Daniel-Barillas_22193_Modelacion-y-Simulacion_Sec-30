"""Algoritmos para generar variables aleatorias continuas y procesos de Poisson."""

from .simulations import (
    SimulationError,
    exact_aggregate_claim_probability,
    generate_normal_exponential_rejection,
    generate_normal_polar,
    polar_transform,
    simulate_composition,
    simulate_homogeneous_poisson,
    simulate_insurance_claims,
    simulate_nhpp_comparison,
    simulate_spatial_poisson,
    simulate_truncated_exponential,
)

__all__ = [
    "SimulationError",
    "exact_aggregate_claim_probability",
    "generate_normal_exponential_rejection",
    "generate_normal_polar",
    "polar_transform",
    "simulate_composition",
    "simulate_homogeneous_poisson",
    "simulate_insurance_claims",
    "simulate_nhpp_comparison",
    "simulate_spatial_poisson",
    "simulate_truncated_exponential",
]

