"""Regenera la corrida de referencia utilizada por README e informe.

Este script centraliza los parámetros predeterminados. Si se modifica un
algoritmo, ejecutar primero este archivo y después ``generar_informe.py`` evita
que la documentación conserve resultados obsoletos.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.practica2.simulations import (  # noqa: E402
    generate_normal_exponential_rejection,
    generate_normal_polar,
    simulate_homogeneous_poisson,
    simulate_insurance_claims,
    simulate_nhpp_comparison,
    simulate_spatial_poisson,
    simulate_truncated_exponential,
)


SEED = 22193
OUTPUT = ROOT / "data" / "resultados_referencia.json"


def build_results() -> dict:
    exercise_1 = simulate_truncated_exponential(SEED)
    exercise_4 = simulate_insurance_claims(SEED, 50_000)
    exercise_5 = generate_normal_exponential_rejection(SEED, 10_000)
    exercise_6 = simulate_homogeneous_poisson(2.0, 10.0, SEED)
    exercise_7 = simulate_nhpp_comparison(SEED)
    exercise_8 = simulate_spatial_poisson(1.0, 5.0, SEED)
    exercise_9 = generate_normal_polar(SEED, 10_000)
    exercise_10 = simulate_spatial_poisson(1.0, 2.0, SEED)
    return {
        "semilla": SEED,
        "ejercicio_1": {
            "muestras": 1_000,
            "media_estimada": exercise_1.summary.estimate,
            "media_exacta": exercise_1.exact_mean,
            "ic_95": [exercise_1.summary.ci_low, exercise_1.summary.ci_high],
        },
        "ejercicio_4": {
            "replicas": 50_000,
            "probabilidad_estimada": exercise_4.summary.estimate,
            "probabilidad_referencia": exercise_4.exact_probability,
            "ic_95": [exercise_4.summary.ci_low, exercise_4.summary.ci_high],
        },
        "ejercicio_5": {
            "normales": 10_000,
            "media": exercise_5.mean,
            "varianza": exercise_5.variance,
            "aceptacion": exercise_5.acceptance_rate,
            "exponenciales_por_normal": exercise_5.exponentials_generated / 10_000,
            "cuadrados_por_normal": exercise_5.squares_computed / 10_000,
        },
        "ejercicio_6": {
            "lambda": 2.0,
            "T": 10.0,
            "eventos_observados": exercise_6.count,
            "eventos_esperados": exercise_6.expected_count,
        },
        "ejercicio_7": {
            "eventos_esperados": exercise_7.expected_count,
            "global_eventos": exercise_7.global_method.count,
            "global_propuestas": exercise_7.global_method.proposal_count,
            "mejorado_eventos": exercise_7.improved_method.count,
            "mejorado_propuestas": exercise_7.improved_method.proposal_count,
        },
        "ejercicio_8": {
            "lambda": 1.0,
            "R": 5.0,
            "puntos_observados": exercise_8.count,
            "puntos_esperados": exercise_8.expected_count,
        },
        "ejercicio_9": {
            "normales": 10_000,
            "media": exercise_9.mean,
            "varianza": exercise_9.variance,
            "aceptacion": exercise_9.acceptance_rate,
        },
        "ejercicio_10": {
            "lambda": 1.0,
            "R": 2.0,
            "puntos_observados": exercise_10.count,
            "puntos_esperados": exercise_10.expected_count,
        },
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(build_results(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Resultados generados: {OUTPUT}")


if __name__ == "__main__":
    main()
