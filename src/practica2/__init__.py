"""API pública de generación continua y procesos de Poisson.

Este módulo reexporta las operaciones que necesita la interfaz y oculta los
auxiliares internos de validación, resumen y construcción de tablas. Mantener
una lista ``__all__`` explícita documenta qué funciones forman parte del contrato
estable del paquete.
"""

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
