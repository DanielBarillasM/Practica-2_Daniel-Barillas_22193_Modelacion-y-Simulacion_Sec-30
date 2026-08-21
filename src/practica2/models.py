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
    """Salida del Ejercicio 1.

    ``samples`` conserva cada uniforme, el valor transformado y la media
    acumulada. ``summary`` contiene la inferencia Monte Carlo, mientras que
    ``exact_mean`` permite compararla con la integral analítica solicitada.
    El límite ``upper`` se conserva para que la interfaz pueda dibujar la
    densidad teórica sobre el soporte correcto.
    """

    samples: pd.DataFrame
    summary: EstimateSummary
    exact_mean: float
    upper: float


@dataclass(frozen=True)
class CompositionResult:
    """Resultado común para los Ejercicios 2 y 3.

    La tabla de muestras registra qué componente de la mezcla se seleccionó y
    cómo se transformó el segundo uniforme. ``comparison`` contiene una malla
    de CDF teórica y empírica lista para graficar. ``powers`` es ``None`` solo
    en el inciso 3(b), que mezcla una exponencial y una uniforme en lugar de
    distribuciones con CDF potencia.
    """

    samples: pd.DataFrame
    comparison: pd.DataFrame
    weights: np.ndarray
    powers: np.ndarray | None
    case: str


@dataclass(frozen=True)
class InsuranceResult:
    """Resumen de la simulación de pérdidas agregadas del Ejercicio 4.

    ``months`` contiene una réplica por fila. El desglose de la primera réplica
    demuestra que el monto Gamma usado para las corridas masivas equivale a
    sumar reclamaciones exponenciales individuales. La probabilidad exacta se
    conserva únicamente como referencia de validación.
    """

    months: pd.DataFrame
    first_month_claims: pd.DataFrame
    summary: EstimateSummary
    exact_probability: float
    expected_aggregate: float


@dataclass(frozen=True)
class NormalRejectionResult:
    """Diagnóstico completo del rechazo exponencial del Ejercicio 5.

    ``attempts`` incluye propuestas aceptadas y rechazadas; ``samples`` solo
    incluye las normales terminadas. Los dos contadores de operaciones permiten
    verificar la eficiencia indicada en el material: cerca de 1.64
    exponenciales y 1.32 cuadrados por normal cuando se recicla el residual.
    """

    samples: pd.DataFrame
    attempts: pd.DataFrame
    mean: float
    variance: float
    acceptance_rate: float
    theoretical_acceptance: float
    exponentials_generated: int
    squares_computed: int


@dataclass(frozen=True)
class PoissonProcessResult:
    """Trayectoria de un proceso de Poisson homogéneo en ``[0,T]``.

    ``events`` conserva incluso el último candidato que supera el horizonte y
    detiene el algoritmo. ``path`` agrega los puntos necesarios para dibujar la
    función escalonada de conteo ``N(t)``.
    """

    events: pd.DataFrame
    path: pd.DataFrame
    count: int
    expected_count: float
    rate: float
    horizon: float


@dataclass(frozen=True)
class NHPPMethodResult:
    """Una ejecución de adelgazamiento para el Ejercicio 7.

    Se separan los eventos aceptados de todas las propuestas para poder auditar
    la razón ``lambda(t)/M`` y medir la tasa de aceptación de cada estrategia de
    cota sin perder información.
    """

    events: pd.DataFrame
    proposals: pd.DataFrame
    count: int
    proposal_count: int
    acceptance_rate: float
    method: str


@dataclass(frozen=True)
class NHPPComparisonResult:
    """Agrupa la estrategia global y la mejorada del proceso no homogéneo.

    Las dos trayectorias usan flujos independientes derivados de una misma
    semilla. Por eso la comparación relevante es la cantidad de propuestas y
    no la igualdad evento por evento.
    """

    global_method: NHPPMethodResult
    improved_method: NHPPMethodResult
    expected_count: float
    horizon: float


@dataclass(frozen=True)
class SpatialPoissonResult:
    """Puntos de un proceso de Poisson bidimensional dentro de un disco.

    Además de las coordenadas, conserva el uniforme usado para el conteo
    Poisson. Esto permite reconstruir tanto el número de puntos como las
    transformaciones radial y angular de los Ejercicios 8 y 10.
    """

    points: pd.DataFrame
    count: int
    expected_count: float
    count_uniform: float
    rate: float
    radius: float


@dataclass(frozen=True)
class PolarNormalResult:
    """Pares aceptados, intentos y momentos del método polar de Marsaglia.

    ``values`` contiene exactamente la cantidad de normales solicitada aunque
    el último par produzca un valor adicional. Las tablas completas explican de
    qué intento provino cada par y por qué los demás fueron rechazados.
    """

    pairs: pd.DataFrame
    attempts: pd.DataFrame
    values: np.ndarray
    mean: float
    variance: float
    acceptance_rate: float
