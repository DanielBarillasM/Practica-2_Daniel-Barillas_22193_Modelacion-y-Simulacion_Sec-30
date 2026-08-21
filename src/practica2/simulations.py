"""Algoritmos numéricos de la Práctica 2.

Todos los generadores reciben una semilla explícita y utilizan
``numpy.random.Generator`` con PCG64. La semilla predeterminada se define en la
interfaz, no aquí, para que estas funciones sean reutilizables y fáciles de
probar. Ninguna función depende de Streamlit.

Las tablas conservan los uniformes y las decisiones relevantes. Esto vuelve
auditable cada transformación aleatoria y permite descargar los resultados sin
perder el procedimiento que los produjo.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import binom, gamma, poisson

from .models import (
    CompositionResult,
    EstimateSummary,
    InsuranceResult,
    NHPPComparisonResult,
    NHPPMethodResult,
    NormalRejectionResult,
    PoissonProcessResult,
    PolarNormalResult,
    SpatialPoissonResult,
    TruncatedExponentialResult,
)


class SimulationError(ValueError):
    """Error de parámetros comprensible para mostrar directamente en la UI."""


Z_95 = 1.959963984540054


def _validate_sample_size(size: int, *, minimum: int = 10, maximum: int = 1_000_000) -> int:
    """Valida tamaños antes de reservar arreglos potencialmente grandes.

    La conversión explícita a entero normaliza valores provenientes de widgets
    numéricos de Streamlit. Los límites evitan muestras vacías y protegen la
    aplicación contra reservas accidentales de memoria excesiva.
    """

    clean_size = int(size)
    if not minimum <= clean_size <= maximum:
        raise SimulationError(
            f"La cantidad solicitada debe estar entre {minimum:,} y {maximum:,}."
        )
    return clean_size


def _estimate_summary(values: np.ndarray) -> EstimateSummary:
    """Calcula media, error estándar e intervalo normal aproximado del 95 %.

    El intervalo es ``media ± z*SE`` con el cuantil normal 0.975. Se utiliza
    ``ddof=1`` para estimar la desviación estándar a partir de la muestra; el
    caso de una sola observación se trata aparte para evitar una división sin
    grados de libertad.
    """

    data = np.asarray(values, dtype=float)
    if data.size == 0:
        raise SimulationError("No se puede resumir una muestra vacía.")
    # Esta función también resume indicadores 0/1; en ese caso la media es una
    # probabilidad Monte Carlo, como ocurre con las reclamaciones del Ejercicio 4.
    estimate = float(np.mean(data))
    standard_error = (
        0.0 if data.size == 1 else float(np.std(data, ddof=1) / math.sqrt(data.size))
    )
    margin = Z_95 * standard_error
    return EstimateSummary(estimate, standard_error, estimate - margin, estimate + margin)


# ---------------------------------------------------------------------------
# Ejercicio 1: exponencial truncada
# ---------------------------------------------------------------------------


def truncated_exponential_exact_mean(upper: float = 0.05) -> float:
    """Devuelve ``E[X | X < upper]`` para ``X ~ Exp(1)``.

    La forma ``1 - a/expm1(a)`` es numéricamente estable cuando ``a`` es muy
    pequeño, pues ``expm1(a)`` calcula ``exp(a)-1`` sin cancelación severa.
    """

    if not math.isfinite(upper) or upper <= 0:
        raise SimulationError("El límite de truncamiento debe ser positivo.")
    return 1.0 - upper / math.expm1(upper)


def simulate_truncated_exponential(
    seed: int,
    sample_size: int = 1_000,
    upper: float = 0.05,
) -> TruncatedExponentialResult:
    """Genera una exponencial de tasa 1 condicionada a ``0 < X < upper``.

    La CDF condicional es ``(1-exp(-x))/(1-exp(-upper))``. Al igualarla a un
    uniforme y despejar se obtiene
    ``X=-log(1-U*(1-exp(-upper)))``. Este método nunca desperdicia propuestas,
    a diferencia de generar exponenciales hasta encontrar una menor que 0.05.
    """

    # El PDF fija n=1,000 desde la interfaz, pero la función admite otros tamaños
    # para facilitar pruebas estadísticas sin duplicar el algoritmo.
    n = _validate_sample_size(sample_size, minimum=1)
    exact = truncated_exponential_exact_mean(upper)
    rng = np.random.default_rng(int(seed))
    uniforms = rng.random(n)
    # ``expm1`` y ``log1p`` evitan pérdida de precisión: a=0.05 hace que las
    # diferencias 1-exp(-a) y 1-U*c sean pequeñas.
    normalization = -math.expm1(-upper)  # 1-exp(-upper), calculado con estabilidad.
    generated = -np.log1p(-uniforms * normalization)
    contributions = generated
    # La trayectoria acumulada no interviene en la estimación final; se conserva
    # como evidencia visual de la ley de los grandes números.
    cumulative = np.cumsum(contributions) / np.arange(1, n + 1)
    samples = pd.DataFrame(
        {
            "Muestra": np.arange(1, n + 1),
            "U": uniforms,
            "X condicionada": generated,
            "Media acumulada": cumulative,
        }
    )
    return TruncatedExponentialResult(samples, _estimate_summary(generated), exact, upper)


# ---------------------------------------------------------------------------
# Ejercicios 2 y 3: composición
# ---------------------------------------------------------------------------


def _validate_weights(weights: Sequence[float]) -> np.ndarray:
    """Normaliza y valida las probabilidades de selección de una mezcla.

    No se renormalizan pesos incorrectos de forma silenciosa. Exigir que sumen
    uno hace visible un error de entrada y conserva exactamente el algoritmo de
    composición planteado en el Ejercicio 2.
    """

    clean = np.asarray(weights, dtype=float)
    if clean.ndim != 1 or clean.size == 0:
        raise SimulationError("Debe existir al menos un peso de composición.")
    if np.any(~np.isfinite(clean)) or np.any(clean < 0):
        raise SimulationError("Los pesos deben ser finitos y no negativos.")
    if not math.isclose(float(clean.sum()), 1.0, abs_tol=1e-10):
        raise SimulationError("Los pesos de composición deben sumar 1.")
    return clean


def simulate_composition(
    case: str,
    sample_size: int,
    seed: int,
    weights: Sequence[float] | None = None,
) -> CompositionResult:
    """Simula las mezclas de los ejercicios 2 y 3.

    Casos disponibles:

    ``general``
        Demostración editable del ejercicio 2. Cada componente tiene CDF
        ``F_i(x)=x^i`` en [0,1] y el usuario proporciona sus pesos.
    ``a``
        Mezcla equiprobable de CDF ``x``, ``x^3`` y ``x^5``.
    ``b``
        Mezcla: exponencial de tasa 2 con peso 1/3 y uniforme(0,1) con 2/3.
    ``c``
        Mezcla general ``sum(alpha_i*x^i)`` usando los pesos proporcionados.
    """

    n = _validate_sample_size(sample_size)
    clean_case = case.lower().strip()
    # Cada caso solo cambia las distribuciones componentes. La selección del
    # índice y el segundo uniforme siguen la misma construcción del Ejercicio 2.
    if clean_case == "a":
        clean_weights = np.array([1 / 3, 1 / 3, 1 / 3], dtype=float)
        powers = np.array([1, 3, 5], dtype=int)
    elif clean_case == "b":
        clean_weights = np.array([1 / 3, 2 / 3], dtype=float)
        powers = None
    elif clean_case in {"c", "general"}:
        clean_weights = _validate_weights(weights if weights is not None else [0.2, 0.3, 0.5])
        powers = np.arange(1, len(clean_weights) + 1, dtype=int)
    else:
        raise SimulationError("El caso de composición debe ser general, a, b o c.")

    rng = np.random.default_rng(int(seed))
    # Un primer uniforme selecciona el componente mediante la CDF discreta de
    # los pesos. ``searchsorted`` implementa transformación inversa discreta.
    u_component = rng.random(n)
    component_index = np.searchsorted(
        np.cumsum(clean_weights), u_component, side="right"
    )
    component_index = np.minimum(component_index, len(clean_weights) - 1)
    # El segundo uniforme debe ser independiente del usado para elegir I; así la
    # distribución condicional dentro de cada componente permanece correcta.
    u_value = rng.random(n)

    if clean_case == "b":
        exponential_component = component_index == 0
        # En 3(b), I=1 genera Exp(2) y I=2 genera Uniforme(0,1). Sus pesos 1/3 y
        # 2/3 reproducen exactamente ambas ramas de la CDF por tramos.
        generated = np.where(
            exponential_component,
            -np.log1p(-u_value) / 2.0,
            u_value,
        )
        component_names = np.where(
            exponential_component,
            "Exponencial(tasa=2)",
            "Uniforme(0,1)",
        )
    else:
        assert powers is not None
        # Si F_i(x)=x^i en [0,1], su inversa es F_i^{-1}(u)=u^(1/i).
        selected_power = powers[component_index]
        generated = np.power(u_value, 1.0 / selected_power)
        component_names = np.array([f"F(x)=x^{power}" for power in selected_power])

    samples = pd.DataFrame(
        {
            "Muestra": np.arange(1, n + 1),
            "U para componente": u_component,
            "Componente": component_index + 1,
            "Distribución elegida": component_names,
            "U para valor": u_value,
            "X generada": generated,
        }
    )

    # La exponencial del inciso (b) no tiene soporte acotado. El percentil 99.5
    # mantiene legible la gráfica sin alterar ninguna muestra ni estadístico.
    max_x = max(1.0, float(np.quantile(generated, 0.995))) if clean_case == "b" else 1.0
    grid = np.linspace(0.0, max_x, 240)
    # La CDF empírica se evalúa contando observaciones <= x en una muestra
    # ordenada. Esta comparación sirve como comprobación, no como generador.
    empirical = np.searchsorted(np.sort(generated), grid, side="right") / n
    if clean_case == "b":
        theoretical = np.where(
            grid < 1,
            (1 - np.exp(-2 * grid) + 2 * grid) / 3,
            (3 - np.exp(-2 * grid)) / 3,
        )
    else:
        assert powers is not None
        theoretical = sum(
            weight * np.power(grid, power)
            for weight, power in zip(clean_weights, powers)
        )
    comparison = pd.DataFrame(
        {"x": grid, "F teórica": theoretical, "F empírica": empirical}
    )
    return CompositionResult(samples, comparison, clean_weights, powers, clean_case)


# ---------------------------------------------------------------------------
# Ejercicio 4: cartera de seguros
# ---------------------------------------------------------------------------


def exact_aggregate_claim_probability(
    insured: int = 1_000,
    claim_probability: float = 0.05,
    claim_mean: float = 800.0,
    threshold: float = 50_000.0,
) -> float:
    """Calcula la referencia exacta de la cola de una suma binomial compuesta.

    Condicionado a ``N=n`` reclamaciones, la suma de ``n`` exponenciales tiene
    distribución Gamma con forma ``n`` y escala ``claim_mean``. Por tanto se
    suma la cola Gamma ponderada por la PMF binomial de ``N``.
    """

    if insured <= 0 or not 0 <= claim_probability <= 1:
        raise SimulationError("Los parámetros de la cartera no son válidos.")
    if claim_mean <= 0 or threshold < 0:
        raise SimulationError("La media y el umbral deben ser válidos.")
    # N=0 no contribuye a la cola cuando el umbral es positivo, de modo que la
    # suma puede iniciar en una reclamación sin término especial.
    counts = np.arange(1, insured + 1)
    # La independencia permite condicionar por N. El producto de la PMF
    # binomial y la supervivencia Gamma integra todas las cantidades posibles.
    probabilities = binom.pmf(counts, insured, claim_probability)
    tails = gamma.sf(threshold, a=counts, scale=claim_mean)
    return float(np.dot(probabilities, tails))


def simulate_insurance_claims(
    seed: int,
    replications: int = 50_000,
    insured: int = 1_000,
    claim_probability: float = 0.05,
    claim_mean: float = 800.0,
    threshold: float = 50_000.0,
) -> InsuranceResult:
    """Simula la pérdida mensual agregada de la compañía de seguros.

    Se genera el número de reclamaciones como binomial. Condicionado a ese
    número, la suma se genera directamente como Gamma; esto es exactamente
    equivalente a sumar exponenciales una por una y evita trabajo innecesario.
    Para auditar el procedimiento, la primera réplica sí muestra sus montos
    individuales, generados en un flujo independiente derivado de la semilla.
    """

    n = _validate_sample_size(replications, minimum=100, maximum=500_000)
    if insured <= 0 or not 0 < claim_probability < 1:
        raise SimulationError("Asegurados y probabilidad deben ser positivos y válidos.")
    if claim_mean <= 0 or threshold <= 0:
        raise SimulationError("La media y el umbral deben ser positivos.")

    # Se derivan flujos independientes: uno produce los agregados y otro detalla
    # la primera réplica. Esto evita que mostrar el detalle cambie las restantes.
    seed_sequence = np.random.SeedSequence(int(seed))
    aggregate_seed, detail_seed = seed_sequence.spawn(2)
    rng = np.random.default_rng(aggregate_seed)
    # Cada fila representa un mes completo. La binomial resume los 1,000
    # indicadores Bernoulli de reclamación sin generar una matriz enorme.
    claim_counts = rng.binomial(insured, claim_probability, size=n)
    totals = np.zeros(n, dtype=float)
    # La primera réplica se desglosa reclamación por reclamación. Las restantes
    # usan la suma Gamma equivalente para mantener eficiente una corrida grande.
    detail_rng = np.random.default_rng(detail_seed)
    first_count = int(claim_counts[0])
    individual = detail_rng.exponential(claim_mean, size=first_count)
    totals[0] = float(individual.sum())
    # Para n>0, la suma de n exponenciales de igual escala es Gamma(n, escala).
    # Solo se llama al generador Gamma en meses con al menos una reclamación.
    positive_indices = np.flatnonzero(claim_counts[1:] > 0) + 1
    totals[positive_indices] = rng.gamma(
        shape=claim_counts[positive_indices], scale=claim_mean
    )
    # El indicador 0/1 convierte directamente su media en la probabilidad
    # estimada de exceder el umbral.
    exceeded = totals > threshold
    running = np.cumsum(exceeded) / np.arange(1, n + 1)
    months = pd.DataFrame(
        {
            "Mes simulado": np.arange(1, n + 1),
            "Número de reclamaciones": claim_counts,
            "Monto agregado": totals,
            "¿Excede el umbral?": np.where(exceeded, "Sí", "No"),
            "Probabilidad acumulada": running,
        }
    )

    first_month_claims = pd.DataFrame(
        {
            "Reclamación": np.arange(1, first_count + 1),
            "Monto individual ilustrativo": individual,
            "Monto acumulado ilustrativo": np.cumsum(individual),
        }
    )
    indicators = exceeded.astype(float)
    exact = exact_aggregate_claim_probability(
        insured, claim_probability, claim_mean, threshold
    )
    return InsuranceResult(
        months=months,
        first_month_claims=first_month_claims,
        summary=_estimate_summary(indicators),
        exact_probability=exact,
        expected_aggregate=insured * claim_probability * claim_mean,
    )


# ---------------------------------------------------------------------------
# Ejercicios 5 y 9: generación normal
# ---------------------------------------------------------------------------


def generate_normal_exponential_rejection(
    seed: int,
    sample_size: int = 10_000,
) -> NormalRejectionResult:
    """Genera normales estándar mediante el Ejemplo 5f del PDF.

    En cada intento se usan ``Y1,Y2 ~ Exp(1)`` independientes y se acepta
    ``Y1`` si ``Y2 > (Y1-1)^2/2``. El residual
    ``Y2-(Y1-1)^2/2`` de un intento aceptado es una exponencial independiente
    del valor normal, por lo que se recicla como ``Y1`` para la siguiente
    normal. Esta es la optimización descrita en el material: en régimen estable
    requiere aproximadamente 1.64 exponenciales y 1.32 cuadrados por normal.
    """

    n = _validate_sample_size(sample_size, minimum=100, maximum=200_000)
    rng = np.random.default_rng(int(seed))
    accepted_rows: list[dict[str, float | int]] = []
    attempt_rows: list[dict[str, float | int | str]] = []
    attempt = 0
    exponentials_generated = 0
    squares_computed = 0
    recycled_y1: float | None = None
    # ``recycled_y1`` lleva entre iteraciones la exponencial residual demostrada
    # independiente en el Ejemplo 5f. Solo la primera normal empieza sin ella.
    while len(accepted_rows) < n:
        if recycled_y1 is None:
            y1 = float(rng.exponential())
            exponentials_generated += 1
            y1_origin = "Generada"
        else:
            y1 = recycled_y1
            recycled_y1 = None
            y1_origin = "Residual reciclada"

        # Una normal puede necesitar varios intentos. Cada intento evalúa una
        # sola condición cuadrática y siempre genera una nueva Y2.
        while True:
            attempt += 1
            y2 = float(rng.exponential())
            exponentials_generated += 1
            # Esta desigualdad evita calcular explícitamente la exponencial de
            # la probabilidad de aceptación del rechazo clásico.
            threshold = 0.5 * (y1 - 1.0) ** 2
            squares_computed += 1
            accepted = y2 > threshold
            residual = y2 - threshold if accepted else float("nan")
            attempt_rows.append(
                {
                    "Intento": attempt,
                    "Origen de Y1": y1_origin,
                    "Y1 exponencial": y1,
                    "Y2 exponencial": y2,
                    "(Y1-1)^2/2": threshold,
                    "Residual exponencial": residual,
                    "Decisión": "Aceptar" if accepted else "Rechazar",
                }
            )
            if accepted:
                # El material demuestra que el residual es Exp(1) e
                # independiente de Z. Se convierte en la Y1 de la próxima
                # normal, evitando generar una exponencial adicional.
                recycled_y1 = residual
                # La densidad normal es simétrica. Una Bernoulli(1/2) aplicada
                # al valor absoluto aceptado recupera la normal estándar.
                u_sign = float(rng.random())
                z = y1 if u_sign <= 0.5 else -y1
                accepted_rows.append(
                    {
                        "Normal generada": len(accepted_rows) + 1,
                        "Intento de origen": attempt,
                        "Valor absoluto": y1,
                        "U para signo": u_sign,
                        "Z": z,
                        "Residual reutilizable": residual,
                    }
                )
                break

            # Después de un rechazo se vuelve al Paso 1 y se genera otra Y1.
            y1 = float(rng.exponential())
            exponentials_generated += 1
            y1_origin = "Generada tras rechazo"
    samples = pd.DataFrame(accepted_rows)
    attempts = pd.DataFrame(attempt_rows)
    values = samples["Z"].to_numpy(dtype=float)
    return NormalRejectionResult(
        samples=samples,
        attempts=attempts,
        mean=float(np.mean(values)),
        variance=float(np.var(values, ddof=1)),
        acceptance_rate=n / attempt,
        theoretical_acceptance=math.sqrt(math.pi / (2 * math.e)),
        exponentials_generated=exponentials_generated,
        squares_computed=squares_computed,
    )


def polar_transform(u1: float, u2: float) -> tuple[float, float, float, float, float]:
    """Aplica un paso aceptado del método polar de Marsaglia.

    Devuelve ``(v1, v2, s, x, y)``. Si el punto cae fuera del círculo unitario
    se lanza ``SimulationError`` para hacer explícita la necesidad de repetir.
    """

    if not (0 < u1 < 1 and 0 < u2 < 1):
        raise SimulationError("U1 y U2 deben pertenecer al intervalo (0,1).")
    # El traslado U -> 2U-1 produce un punto uniforme en el cuadrado (-1,1)^2.
    v1 = 2 * float(u1) - 1
    v2 = 2 * float(u2) - 1
    s = v1 * v1 + v2 * v2
    if s <= 0 or s >= 1:
        raise SimulationError(
            f"El par se rechaza porque S={s:.6f} no pertenece a (0,1)."
        )
    # Condicionado a caer dentro del disco, el factor radial transforma el par
    # uniforme en dos normales estándar independientes sin seno ni coseno.
    factor = math.sqrt(-2 * math.log(s) / s)
    return v1, v2, s, v1 * factor, v2 * factor


def generate_normal_polar(seed: int, sample_size: int = 10_000) -> PolarNormalResult:
    """Genera normales estándar en pares con el método polar de Marsaglia.

    Cada propuesta consume dos uniformes. Si ``S`` no pertenece a ``(0,1)`` se
    rechaza el par completo; una propuesta aceptada produce dos observaciones.
    Si el tamaño solicitado es impar, el segundo valor del último par se omite
    únicamente de ``values`` pero permanece documentado en la tabla de pares.
    """

    n = _validate_sample_size(sample_size, minimum=100, maximum=200_000)
    rng = np.random.default_rng(int(seed))
    pairs: list[dict[str, float | int]] = []
    attempts: list[dict[str, float | int | str]] = []
    values: list[float] = []
    attempt = 0
    while len(values) < n:
        attempt += 1
        u1, u2 = rng.random(2)
        v1 = 2 * float(u1) - 1
        v2 = 2 * float(u2) - 1
        s = v1 * v1 + v2 * v2
        # S=0 haría indefinido ln(S)/S y S>=1 corresponde a la región de rechazo.
        accepted = 0 < s < 1
        attempts.append(
            {
                "Intento": attempt,
                "U1": u1,
                "U2": u2,
                "V1": v1,
                "V2": v2,
                "S": s,
                "Decisión": "Aceptar" if accepted else "Rechazar",
            }
        )
        if not accepted:
            continue
        factor = math.sqrt(-2 * math.log(s) / s)
        x, y = v1 * factor, v2 * factor
        pair_number = len(pairs) + 1
        pairs.append(
            {
                "Par": pair_number,
                "Intento de origen": attempt,
                "S": s,
                "Factor": factor,
                "X": x,
                "Y": y,
            }
        )
        values.append(x)
        if len(values) < n:
            values.append(y)
    array = np.asarray(values[:n], dtype=float)
    return PolarNormalResult(
        pairs=pd.DataFrame(pairs),
        attempts=pd.DataFrame(attempts),
        values=array,
        mean=float(np.mean(array)),
        variance=float(np.var(array, ddof=1)),
        acceptance_rate=len(pairs) / attempt,
    )


# ---------------------------------------------------------------------------
# Ejercicio 6: proceso de Poisson homogéneo
# ---------------------------------------------------------------------------


def simulate_homogeneous_poisson(
    rate: float,
    horizon: float,
    seed: int,
) -> PoissonProcessResult:
    """Genera los eventos de un proceso de Poisson homogéneo en ``[0,T]``."""

    if not math.isfinite(rate) or rate <= 0:
        raise SimulationError("La tasa lambda debe ser positiva.")
    if not math.isfinite(horizon) or horizon <= 0:
        raise SimulationError("El horizonte T debe ser positivo.")
    # Los incrementos exponenciales son independientes y estacionarios; sumar
    # sus realizaciones construye los tiempos de llegada del proceso.
    rng = np.random.default_rng(int(seed))
    time = 0.0
    rows: list[dict[str, float | int | str]] = []
    event_times: list[float] = []
    draw = 0
    while True:
        draw += 1
        u = float(rng.random())
        # Inversa de F_E(t)=1-exp(-lambda*t). ``log1p`` mantiene precisión cerca
        # de U=0 y expresa en la tabla el uniforme que originó cada salto.
        interarrival = -math.log1p(-u) / rate
        candidate = time + interarrival
        inside = candidate <= horizon
        rows.append(
            {
                "Generación": draw,
                "U": u,
                "Tiempo entre llegadas": interarrival,
                "Tiempo candidato": candidate,
                "Resultado": "Evento dentro de [0,T]" if inside else "Supera T; detener",
            }
        )
        # El primer candidato fuera de [0,T] certifica que ya no existen eventos
        # por generar en el horizonte y también se conserva para auditoría.
        if not inside:
            break
        time = candidate
        event_times.append(time)

    events = pd.DataFrame(rows)
    # Repetir el conteo final en T permite que Plotly cierre correctamente el
    # último tramo horizontal de la trayectoria escalonada.
    path_times = [0.0, *event_times, horizon]
    path_counts = [0, *range(1, len(event_times) + 1), len(event_times)]
    path = pd.DataFrame({"Tiempo": path_times, "N(t)": path_counts})
    return PoissonProcessResult(
        events=events,
        path=path,
        count=len(event_times),
        expected_count=rate * horizon,
        rate=rate,
        horizon=horizon,
    )


# ---------------------------------------------------------------------------
# Ejercicio 7: proceso de Poisson no homogéneo
# ---------------------------------------------------------------------------


def nhpp_intensity(time: float | np.ndarray) -> float | np.ndarray:
    """Intensidad del enunciado: ``lambda(t)=3+4/(t+1)``.

    Acepta escalares o arreglos para reutilizar la misma definición tanto en el
    simulador como en la curva mostrada por la interfaz.
    """

    return 3.0 + 4.0 / (np.asarray(time) + 1.0)


def _nhpp_global(horizon: float, rng: np.random.Generator) -> NHPPMethodResult:
    """Aplica thinning con la cota constante ``M=lambda(0)=7``.

    Los candidatos forman un Poisson homogéneo de tasa 7. Aceptar cada candidato
    con probabilidad ``lambda(t)/7`` deja exactamente la intensidad deseada.
    """

    bound = 7.0
    time = 0.0
    rows: list[dict[str, float | int | str]] = []
    accepted_times: list[float] = []
    proposal = 0
    while True:
        u_gap = float(rng.random())
        candidate = time - math.log1p(-u_gap) / bound
        if candidate > horizon:
            break
        time = candidate
        proposal += 1
        intensity = float(nhpp_intensity(time))
        probability = intensity / bound
        u_accept = float(rng.random())
        # El uniforme de aceptación adelgaza el proceso dominante sin mover el
        # reloj: incluso una propuesta rechazada pasa a ser el nuevo tiempo base.
        accepted = u_accept <= probability
        if accepted:
            accepted_times.append(time)
        rows.append(
            {
                "Propuesta": proposal,
                "U para salto": u_gap,
                "Tiempo candidato": time,
                "Cota M": bound,
                "Intensidad lambda(t)": intensity,
                "U de aceptación": u_accept,
                "lambda(t)/M": probability,
                "Decisión": "Aceptar" if accepted else "Rechazar",
            }
        )
    proposals = pd.DataFrame(rows)
    events = pd.DataFrame(
        {"Evento": np.arange(1, len(accepted_times) + 1), "Tiempo": accepted_times}
    )
    return NHPPMethodResult(
        events,
        proposals,
        len(accepted_times),
        proposal,
        0.0 if proposal == 0 else len(accepted_times) / proposal,
        "Cota global M=7",
    )


def _nhpp_piecewise(horizon: float, rng: np.random.Generator) -> NHPPMethodResult:
    """Adelgazamiento mejorado con una cota decreciente por cada intervalo.

    Como la intensidad es monótona decreciente, su valor en el extremo izquierdo
    de ``[k,k+1)`` domina todo ese intervalo. Reiniciar el proceso dominante al
    cambiar de intervalo es válido por la independencia de incrementos Poisson.
    """

    rows: list[dict[str, float | int | str]] = []
    accepted_times: list[float] = []
    proposal = 0
    interval_start = 0.0
    while interval_start < horizon:
        interval_end = min(math.floor(interval_start) + 1.0, horizon)
        # Esta cota local queda mucho más cerca de lambda(t) que la cota global,
        # especialmente al final del horizonte; por eso reduce los rechazos.
        bound = float(nhpp_intensity(interval_start))
        time = interval_start
        while True:
            u_gap = float(rng.random())
            candidate = time - math.log1p(-u_gap) / bound
            # Una propuesta que cruza el límite no pertenece al proceso
            # dominante de este intervalo; se cambia de cota y se reinicia allí.
            if candidate >= interval_end:
                break
            time = candidate
            proposal += 1
            intensity = float(nhpp_intensity(time))
            probability = intensity / bound
            u_accept = float(rng.random())
            accepted = u_accept <= probability
            if accepted:
                accepted_times.append(time)
            rows.append(
                {
                    "Propuesta": proposal,
                    "Intervalo": f"[{interval_start:g}, {interval_end:g})",
                    "U para salto": u_gap,
                    "Tiempo candidato": time,
                    "Cota local M_k": bound,
                    "Intensidad lambda(t)": intensity,
                    "U de aceptación": u_accept,
                    "lambda(t)/M_k": probability,
                    "Decisión": "Aceptar" if accepted else "Rechazar",
                }
            )
        interval_start = interval_end
    accepted_times.sort()
    proposals = pd.DataFrame(rows)
    events = pd.DataFrame(
        {"Evento": np.arange(1, len(accepted_times) + 1), "Tiempo": accepted_times}
    )
    return NHPPMethodResult(
        events,
        proposals,
        len(accepted_times),
        proposal,
        0.0 if proposal == 0 else len(accepted_times) / proposal,
        "Cotas locales por intervalo",
    )


def simulate_nhpp_comparison(seed: int, horizon: float = 10.0) -> NHPPComparisonResult:
    """Compara el adelgazamiento global con la mejora pedida en el inciso (b).

    ``SeedSequence.spawn`` produce dos flujos reproducibles pero independientes.
    Así una estrategia no consume los uniformes de la otra y ambas pueden
    ejecutarse o inspeccionarse por separado.
    """

    if not math.isfinite(horizon) or horizon <= 0:
        raise SimulationError("El horizonte debe ser positivo.")
    seed_sequence = np.random.SeedSequence(int(seed))
    global_seed, improved_seed = seed_sequence.spawn(2)
    global_result = _nhpp_global(horizon, np.random.default_rng(global_seed))
    improved_result = _nhpp_piecewise(horizon, np.random.default_rng(improved_seed))
    # Integral analítica de 3+4/(t+1) entre 0 y T. Es una referencia de media,
    # no el número de eventos que cada trayectoria individual debe alcanzar.
    expected = 3 * horizon + 4 * math.log(horizon + 1)
    return NHPPComparisonResult(global_result, improved_result, expected, horizon)


# ---------------------------------------------------------------------------
# Ejercicios 8 y 10: proceso de Poisson bidimensional
# ---------------------------------------------------------------------------


def _poisson_inverse(mean: float, uniform: float) -> int:
    """Genera Poisson por inversión y conserva el uniforme para la auditoría.

    La función cuantil estable de SciPy evita sumar muchas probabilidades cuando
    ``lambda*pi*R^2`` es grande. La validación mantiene la misma convención
    semiabierta ``[0,1)`` que utiliza ``Generator.random``.
    """

    if not 0 <= uniform < 1:
        raise SimulationError("El uniforme para invertir Poisson debe pertenecer a [0,1).")
    # SciPy adopta la convención ppf(0)=-1 para algunas distribuciones
    # discretas. En la inversión usada aquí, U=0 corresponde correctamente a
    # N=0 porque ya satisface U <= F(0).
    if uniform == 0:
        return 0
    # ``ppf`` implementa la inversión de manera estable incluso cuando
    # exp(-mean) subdesborda para regiones con una cantidad esperada grande.
    count = poisson.ppf(uniform, mean)
    if not np.isfinite(count):
        raise SimulationError("No fue posible completar la inversión Poisson.")
    return int(count)


def simulate_spatial_poisson(
    rate: float,
    radius: float,
    seed: int,
) -> SpatialPoissonResult:
    """Genera un proceso de Poisson espacial homogéneo dentro de un círculo.

    Primero se genera ``N ~ Poisson(lambda*pi*R^2)``. Condicionado a ``N``, los
    puntos son uniformes en el disco. La raíz en ``r=R*sqrt(U)`` corrige el área:
    usar ``r=R*U`` concentraría incorrectamente los puntos cerca del centro.
    """

    if not math.isfinite(rate) or rate <= 0:
        raise SimulationError("La intensidad espacial debe ser positiva.")
    if not math.isfinite(radius) or radius <= 0:
        raise SimulationError("El radio debe ser positivo.")
    # Una región de área A contiene Poisson(lambda*A) puntos. En un disco,
    # A=pi*R^2 determina primero el conteo total.
    mean = rate * math.pi * radius**2
    if mean > 5_000:
        raise SimulationError("El número esperado de puntos no puede exceder 5,000.")
    rng = np.random.default_rng(int(seed))
    # Se usa inversión en lugar de ``rng.poisson`` para poder mostrar también el
    # uniforme responsable del conteo en el ejemplo numérico del Ejercicio 10.
    u_count = float(rng.random())
    count = _poisson_inverse(mean, u_count)
    u_radius = rng.random(count)
    u_angle = rng.random(count)
    # P(r<=x)=x^2/R^2 para un punto uniforme por área. Invertir esa CDF explica
    # la raíz cuadrada; usar R*U concentraría puntos incorrectamente en el centro.
    radial = radius * np.sqrt(u_radius)
    angle = 2 * math.pi * u_angle
    # Las coordenadas cartesianas se calculan solo para visualizar. La tabla
    # conserva además (r,theta), como solicita el ejemplo teórico del PDF.
    x = radial * np.cos(angle)
    y = radial * np.sin(angle)
    points = pd.DataFrame(
        {
            "Punto": np.arange(1, count + 1),
            "U radial": u_radius,
            "U angular": u_angle,
            "Radio r": radial,
            "Ángulo theta (rad)": angle,
            "Coordenada x": x,
            "Coordenada y": y,
        }
    )
    return SpatialPoissonResult(points, count, mean, u_count, rate, radius)
