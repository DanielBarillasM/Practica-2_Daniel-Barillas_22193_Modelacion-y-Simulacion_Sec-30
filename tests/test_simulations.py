"""Pruebas teóricas y prácticas de los algoritmos de la Práctica 2."""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.practica2.simulations import (
    SimulationError,
    _poisson_inverse,
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
    truncated_exponential_exact_mean,
)


def test_truncated_exponential_stays_inside_support_and_matches_mean() -> None:
    """Valida soporte, fórmula exacta y convergencia de la exponencial truncada."""

    result = simulate_truncated_exponential(22193, sample_size=100_000)
    values = result.samples["X condicionada"].to_numpy()
    assert np.all(values > 0)
    assert np.all(values < 0.05)
    assert result.exact_mean == pytest.approx(0.0247916753467, abs=1e-13)
    assert result.summary.estimate == pytest.approx(result.exact_mean, abs=0.00012)


def test_truncated_exponential_rejects_invalid_upper_bound() -> None:
    """Confirma que un límite no positivo no define la condición solicitada."""

    with pytest.raises(SimulationError):
        truncated_exponential_exact_mean(0)


@pytest.mark.parametrize("case", ["a", "b"])
def test_fixed_compositions_match_theoretical_cdf(case: str) -> None:
    """Compara las mezclas fijas de (a) y (b) con sus CDF analíticas."""

    result = simulate_composition(case, 100_000, seed=22193)
    max_error = np.max(np.abs(result.comparison["F teórica"] - result.comparison["F empírica"]))
    assert max_error < 0.008
    assert len(result.samples) == 100_000


def test_general_composition_respects_weights_and_power_components() -> None:
    """Verifica frecuencias de mezcla y soporte para la familia del inciso (c)."""

    result = simulate_composition("c", 100_000, 7, [0.1, 0.2, 0.3, 0.4])
    frequencies = result.samples["Componente"].value_counts(normalize=True).sort_index()
    assert np.allclose(frequencies.to_numpy(), [0.1, 0.2, 0.3, 0.4], atol=0.006)
    assert result.samples["X generada"].between(0, 1, inclusive="neither").all()


def test_composition_rejects_weights_that_do_not_sum_to_one() -> None:
    """Exige que los coeficientes ingresados formen una distribución discreta."""

    with pytest.raises(SimulationError, match="sumar 1"):
        simulate_composition("c", 1_000, 1, [0.2, 0.2])


def test_insurance_reference_and_simulation_are_consistent() -> None:
    """Contrasta la cartera simulada con la suma binomial-Gamma de referencia.

    También comprueba que el detalle ilustrativo del primer mes reconstruye su
    monto agregado y que la esperanza se obtiene con los parámetros del PDF.
    """

    exact = exact_aggregate_claim_probability()
    result = simulate_insurance_claims(22193, replications=100_000)
    assert exact == pytest.approx(0.10709770132248, abs=1e-12)
    assert result.summary.estimate == pytest.approx(exact, abs=0.004)
    assert result.first_month_claims["Monto individual ilustrativo"].sum() == pytest.approx(
        result.months.iloc[0]["Monto agregado"]
    )
    assert result.expected_aggregate == pytest.approx(40_000)


def test_normal_rejection_generates_standard_normal_and_expected_acceptance() -> None:
    """Audita distribución, aceptación y costo del rechazo exponencial.

    Las dos últimas razones comprueban la mejora práctica del reciclaje residual,
    mientras media, varianza y aceptación validan la teoría del generador.
    """

    result = generate_normal_exponential_rejection(22193, 50_000)
    assert result.mean == pytest.approx(0, abs=0.025)
    assert result.variance == pytest.approx(1, abs=0.04)
    assert result.acceptance_rate == pytest.approx(result.theoretical_acceptance, abs=0.01)
    assert (result.attempts["Y2 exponencial"] >= 0).all()
    expected_exponentials = 2 * math.sqrt(2 * math.e / math.pi) - 1
    expected_squares = math.sqrt(2 * math.e / math.pi)
    assert result.exponentials_generated / len(result.samples) == pytest.approx(
        expected_exponentials, abs=0.03
    )
    assert result.squares_computed / len(result.samples) == pytest.approx(
        expected_squares, abs=0.02
    )
    assert "Residual reciclada" in set(result.attempts["Origen de Y1"])


def test_homogeneous_poisson_trace_is_ordered_and_stops_after_horizon() -> None:
    """Revisa orden temporal, regla de parada y conteo de la trayectoria."""

    result = simulate_homogeneous_poisson(2.0, 10.0, 22193)
    accepted = result.events.iloc[:-1]
    assert (accepted["Tiempo candidato"] <= 10).all()
    assert result.events.iloc[-1]["Tiempo candidato"] > 10
    assert accepted["Tiempo candidato"].is_monotonic_increasing
    assert result.path.iloc[-1]["N(t)"] == result.count
    assert result.expected_count == pytest.approx(20)


def test_poisson_counts_have_correct_mean_over_many_independent_runs() -> None:
    """Comprueba empíricamente que E[N(T)] coincide con lambda por T."""

    counts = [simulate_homogeneous_poisson(1.5, 4.0, seed).count for seed in range(1_000)]
    assert np.mean(counts) == pytest.approx(6.0, abs=0.25)


def test_nhpp_thinning_probabilities_and_integrated_intensity_are_valid() -> None:
    """Valida intensidad integrada, probabilidades y dominio de ambos métodos."""

    result = simulate_nhpp_comparison(22193)
    assert result.expected_count == pytest.approx(30 + 4 * math.log(11))
    assert (result.global_method.proposals["lambda(t)/M"].between(0, 1)).all()
    assert (result.improved_method.proposals["lambda(t)/M_k"].between(0, 1)).all()
    assert (result.global_method.events["Tiempo"].between(0, 10)).all()
    assert (result.improved_method.events["Tiempo"].between(0, 10)).all()


def test_spatial_poisson_points_are_inside_circle() -> None:
    """Comprueba la media de área y la coherencia polar-cartesiana de los puntos."""

    result = simulate_spatial_poisson(1.0, 5.0, 22193)
    assert result.expected_count == pytest.approx(25 * math.pi)
    assert (result.points["Radio r"] <= 5).all()
    computed = np.hypot(result.points["Coordenada x"], result.points["Coordenada y"])
    assert np.allclose(computed, result.points["Radio r"])


def test_poisson_inverse_maps_zero_uniform_to_zero_count() -> None:
    """Cubre ambos extremos de entrada de la inversión discreta de Poisson.

    El uniforme cero pertenece al intervalo acumulado del conteo cero, mientras
    que uno queda fuera del soporte permitido para una uniforme en [0,1).
    """

    assert _poisson_inverse(10.0, 0.0) == 0
    with pytest.raises(SimulationError):
        _poisson_inverse(10.0, 1.0)


def test_spatial_poisson_counts_match_area_mean_over_repetitions() -> None:
    """Valida que el promedio espacial siga la ley lambda por área."""

    counts = [simulate_spatial_poisson(1.0, 2.0, seed).count for seed in range(1_000)]
    assert np.mean(counts) == pytest.approx(4 * math.pi, abs=0.5)


def test_polar_numerical_example_and_distribution() -> None:
    """Reproduce el ejemplo manual y verifica la normal generada por Marsaglia."""

    v1, v2, s, x, y = polar_transform(0.70, 0.40)
    assert (v1, v2, s) == pytest.approx((0.4, -0.2, 0.2))
    assert (x, y) == pytest.approx((1.6047120177, -0.8023560089), abs=1e-9)
    result = generate_normal_polar(22193, 50_000)
    assert result.mean == pytest.approx(0, abs=0.025)
    assert result.variance == pytest.approx(1, abs=0.04)
    assert result.acceptance_rate == pytest.approx(math.pi / 4, abs=0.01)


def test_polar_method_explicitly_rejects_outside_pair() -> None:
    """Confirma la regla geométrica que descarta pares fuera del círculo unitario."""

    with pytest.raises(SimulationError, match="rechaza"):
        polar_transform(0.99, 0.99)
