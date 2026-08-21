"""Interfaz Streamlit de la Práctica 2 de Modelación y Simulación.

La interfaz contiene las respuestas teóricas y las demostraciones numéricas de
los diez ejercicios del PDF. La lógica aleatoria vive en ``src/practica2`` para
que el código matemático pueda probarse sin iniciar Streamlit.

Ejecutar desde la raíz del repositorio con::

    streamlit run app/app.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ``streamlit run app/app.py`` agrega la carpeta app al path. Se incorpora la
# raíz explícitamente para importar el paquete de cálculo ubicado en src.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.practica2.models import (  # noqa: E402
    CompositionResult,
    InsuranceResult,
    NHPPComparisonResult,
    NormalRejectionResult,
    PoissonProcessResult,
    PolarNormalResult,
    SpatialPoissonResult,
    TruncatedExponentialResult,
)
from src.practica2.simulations import (  # noqa: E402
    SimulationError,
    generate_normal_exponential_rejection,
    generate_normal_polar,
    nhpp_intensity,
    polar_transform,
    simulate_composition,
    simulate_homogeneous_poisson,
    simulate_insurance_claims,
    simulate_nhpp_comparison,
    simulate_spatial_poisson,
    simulate_truncated_exponential,
)


st.set_page_config(
    page_title="Práctica 2 | Variables Aleatorias Continuas",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def _load_css() -> None:
    """Carga la hoja de estilos sin mezclar CSS extenso con la lógica de UI."""

    css_path = ROOT / "assets" / "styles.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


_load_css()

REPOSITORY_URL = (
    "https://github.com/DanielBarillasM/"
    "Practica-2_Daniel-Barillas_22193_Modelacion-y-Simulacion_Sec-30"
)
DEFAULT_SEED = 22193

ACADEMIC_HEADER = f"""
<section class="academic-header">
  <div>
    <div class="institution">UNIVERSIDAD DEL VALLE DE GUATEMALA</div>
    <div class="faculty">Facultad de Ingeniería · Ciencia de la Computación y Tecnologías de la Información</div>
  </div>
  <div class="academic-grid">
    <div class="academic-field"><span>Curso</span><strong>CC2017 · Modelación y Simulación</strong></div>
    <div class="academic-field"><span>Período</span><strong>Ciclo 2, 2026 · Sección 30</strong></div>
    <div class="academic-field"><span>Estudiante</span><strong>Pablo Daniel Barillas Moreno</strong></div>
    <div class="academic-field"><span>Carné</span><strong>22193</strong></div>
  </div>
</section>
<section class="hero">
  <div class="hero-kicker">CC2017 · Práctica 2</div>
  <h1>Generación de Variables Aleatorias Continuas</h1>
  <p>Teoría, algoritmos auditables, simulación, convergencia y procesos de Poisson.</p>
</section>
"""

NAVIGATION = [
    "1. Exponencial condicionada",
    "2. Método de composición",
    "3. Distribuciones por composición",
    "4. Cartera de seguros",
    "5. Normal por rechazo exponencial",
    "6. Proceso de Poisson homogéneo",
    "7. Poisson no homogéneo",
    "8. Poisson bidimensional",
    "9. Método polar",
    "10. Proceso bidimensional: teoría",
]


def format_number(value: float, digits: int = 6) -> str:
    """Presenta valores de distintas escalas sin ocultar cifras relevantes."""

    if not math.isfinite(value):
        return "No disponible"
    if value == 0:
        return "0"
    if abs(value) >= 1_000_000 or abs(value) < 1e-4:
        return f"{value:.5e}"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def section_intro(title: str, description: str) -> None:
    st.header(title)
    st.markdown(
        f'<div class="section-intro"><p>{description}</p></div>',
        unsafe_allow_html=True,
    )


def exercise_statement(text: str) -> None:
    """Presenta el enunciado del PDF antes de desarrollar la solución."""

    st.subheader("Enunciado del ejercicio")
    st.info(text)


def theory_card(text: str) -> None:
    st.markdown(f'<div class="theory-card">{text}</div>', unsafe_allow_html=True)


def download_table(data: pd.DataFrame, filename: str, key: str) -> None:
    st.download_button(
        "Descargar tabla completa en CSV",
        data=data.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def normal_histogram(values: np.ndarray, title: str) -> go.Figure:
    figure = px.histogram(
        x=values,
        histnorm="probability density",
        nbins=55,
        labels={"x": "Valor generado", "y": "Densidad"},
        title=title,
        color_discrete_sequence=["#08783f"],
        opacity=0.72,
    )
    grid = np.linspace(-4, 4, 500)
    density = np.exp(-(grid**2) / 2) / math.sqrt(2 * math.pi)
    figure.add_trace(go.Scatter(x=grid, y=density, name="N(0,1) teórica", line=dict(color="#d99000", width=3)))
    return figure


def spatial_figure(result: SpatialPoissonResult, title: str) -> go.Figure:
    angle = np.linspace(0, 2 * math.pi, 500)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=result.radius * np.cos(angle),
            y=result.radius * np.sin(angle),
            mode="lines",
            name="Frontera del círculo",
            line=dict(color="#064d2d", width=2),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=result.points["Coordenada x"],
            y=result.points["Coordenada y"],
            mode="markers",
            name="Puntos del proceso",
            marker=dict(color="#d99000", size=8, line=dict(color="#7d5300", width=0.5)),
            text=result.points["Punto"],
        )
    )
    figure.update_layout(title=title, xaxis_title="x", yaxis_title="y", height=610)
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return figure


# ---------------------------------------------------------------------------
# Ejercicio 1
# ---------------------------------------------------------------------------


def exercise_1_page() -> None:
    section_intro(
        "Ejercicio 1 · Exponencial condicionada",
        "Generación eficiente de 1,000 valores de una exponencial de media 1 condicionada a X < 0.05.",
    )
    exercise_statement(
        r"Sea $X$ una variable aleatoria exponencial con media 1. Proporcione un algoritmo eficiente "
        r"para simular una variable aleatoria cuya distribución es la distribución condicional de $X$ "
        r"dado que $X<0.05$, con densidad $f(x)=e^{-x}/(1-e^{-0.05})$ para $0<x<0.05$. "
        r"Genere 1,000 de estas variables y utilícelas para estimar $E[X\mid X<0.05]$. "
        r"Luego determine el valor exacto de $E[X\mid X<0.05]$."
    )
    theory_card(
        "<strong>Idea central.</strong> Rechazar exponenciales mayores que 0.05 desperdiciaría "
        "aproximadamente el 95 % de las propuestas. La transformación inversa genera directamente "
        "dentro del intervalo requerido."
    )
    st.latex(r"F_c(x)=P(X\le x\mid X<a)=\frac{1-e^{-x}}{1-e^{-a}},\qquad 0<x<a")
    st.latex(r"X=-\ln\!\left(1-U(1-e^{-a})\right),\qquad a=0.05")
    with st.expander("Derivación del valor exacto", expanded=True):
        st.latex(
            r"E[X\mid X<a]=\frac{\int_0^a xe^{-x}\,dx}{1-e^{-a}}"
            r"=\frac{1-(a+1)e^{-a}}{1-e^{-a}}=1-\frac{a}{e^a-1}"
        )
        st.latex(r"E[X\mid X<0.05]\approx 0.02479167535")

    with st.form("exercise_1_form"):
        seed = st.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex1_seed")
        st.caption("El enunciado exige exactamente 1,000 variables; esa cantidad permanece fija.")
        submitted = st.form_submit_button("Generar 1,000 variables", type="primary", width="stretch")
    if submitted:
        st.session_state["ex1_result"] = simulate_truncated_exponential(int(seed))
    if "ex1_result" not in st.session_state:
        st.info("Ejecuta el algoritmo para ver la estimación, la convergencia y las 1,000 transformaciones.")
        return

    result: TruncatedExponentialResult = st.session_state["ex1_result"]
    summary = result.summary
    cols = st.columns(5)
    cols[0].metric("Media estimada", format_number(summary.estimate, 9))
    cols[1].metric("Media exacta", format_number(result.exact_mean, 9))
    cols[2].metric("Error absoluto", format_number(abs(summary.estimate - result.exact_mean), 9))
    cols[3].metric("Error estándar", format_number(summary.standard_error, 9))
    cols[4].metric("IC aproximado 95 %", f"[{summary.ci_low:.6f}, {summary.ci_high:.6f}]")

    dist_tab, convergence_tab, table_tab = st.tabs(["Distribución", "Convergencia", "Todas las muestras"])
    with dist_tab:
        figure = px.histogram(
            result.samples,
            x="X condicionada",
            nbins=35,
            histnorm="probability density",
            title="Exponencial truncada generada por transformación inversa",
            color_discrete_sequence=["#08783f"],
        )
        grid = np.linspace(0, result.upper, 300)
        density = np.exp(-grid) / (1 - math.exp(-result.upper))
        figure.add_trace(go.Scatter(x=grid, y=density, name="Densidad teórica", line=dict(color="#d99000", width=3)))
        st.plotly_chart(figure)
    with convergence_tab:
        figure = px.line(result.samples, x="Muestra", y="Media acumulada", title="Convergencia hacia la esperanza condicional")
        figure.add_hline(y=result.exact_mean, line_dash="dash", line_color="#d99000", annotation_text="Valor exacto")
        st.plotly_chart(figure)
    with table_tab:
        st.dataframe(result.samples, width="stretch", hide_index=True, height=520)
        download_table(result.samples, "ejercicio_1_exponencial_condicionada.csv", "download_ex1")


# ---------------------------------------------------------------------------
# Ejercicio 2
# ---------------------------------------------------------------------------


def _parse_weights(text: str) -> list[float]:
    try:
        values = [float(piece) for piece in re.split(r"[,;\s]+", text.strip()) if piece]
    except ValueError as exc:
        raise SimulationError("Los pesos deben ser números separados por comas.") from exc
    if not values:
        raise SimulationError("Escribe al menos un peso.")
    return values


def exercise_2_page() -> None:
    section_intro(
        "Ejercicio 2 · Método de composición",
        "Respuesta teórica y demostración programada para generar una distribución que es mezcla de varias CDF.",
    )
    exercise_statement(
        r"Suponga que es relativamente fácil generar variables aleatorias a partir de cualquiera de "
        r"las distribuciones $F_i$, $i=1,\ldots,n$. ¿Cómo podríamos generar una variable aleatoria con "
        r"función de distribución $F(x)=\sum_{i=1}^{n}p_iF_i(x)$, donde los $p_i$ son números no "
        r"negativos cuya suma es 1?"
    )
    st.subheader("Respuesta teórica")
    st.markdown(
        "Se introduce una variable discreta auxiliar $I$. Primero se selecciona la distribución "
        "que producirá la observación y luego se genera el valor continuo condicionado a esa selección."
    )
    st.latex(r"P(I=i)=p_i,\qquad i=1,\ldots,n")
    st.code(
        "1. Generar el índice I con probabilidades p_1, ..., p_n.\n"
        "2. Condicionado a I=i, generar X utilizando F_i.\n"
        "3. Devolver X.",
        language="text",
    )
    with st.expander("Demostración de que el algoritmo produce F", expanded=True):
        st.latex(
            r"P(X\le x)=\sum_{i=1}^{n}P(I=i)P(X\le x\mid I=i)"
            r"=\sum_{i=1}^{n}p_iF_i(x)=F(x)"
        )
        st.write("La igualdad se obtiene por la ley de la probabilidad total.")

    theory_card(
        "<strong>Demostración interactiva.</strong> Para hacer observable el método se usan componentes "
        "con CDF F_i(x)=x^i en [0,1]. Los pesos pueden editarse y deben sumar exactamente 1."
    )
    with st.form("exercise_2_form"):
        col1, col2, col3 = st.columns(3)
        weights_text = col1.text_input("Pesos p_i", "0.40, 0.60")
        sample_size = col2.number_input("Muestras", 100, 200_000, 10_000, 100)
        seed = col3.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex2_seed")
        submitted = st.form_submit_button("Demostrar composición", type="primary", width="stretch")
    if submitted:
        try:
            st.session_state["ex2_result"] = simulate_composition(
                "general", int(sample_size), int(seed), _parse_weights(weights_text)
            )
        except SimulationError as exc:
            st.error(str(exc))
            st.session_state.pop("ex2_result", None)
    if "ex2_result" not in st.session_state:
        return
    result: CompositionResult = st.session_state["ex2_result"]
    chart_tab, frequencies_tab, table_tab = st.tabs(["CDF teórica y empírica", "Componentes", "Todas las muestras"])
    with chart_tab:
        figure = px.line(result.comparison, x="x", y=["F teórica", "F empírica"], title="Verificación de la mezcla")
        st.plotly_chart(figure)
    with frequencies_tab:
        counts = result.samples["Componente"].value_counts().sort_index()
        comparison = pd.DataFrame(
            {
                "Componente": np.arange(1, len(result.weights) + 1),
                "Peso teórico": result.weights,
                "Proporción empírica": [counts.get(i, 0) / len(result.samples) for i in range(1, len(result.weights) + 1)],
            }
        )
        st.dataframe(comparison, width="stretch", hide_index=True)
    with table_tab:
        st.dataframe(result.samples, width="stretch", hide_index=True, height=520)
        download_table(result.samples, "ejercicio_2_composicion.csv", "download_ex2")


# ---------------------------------------------------------------------------
# Ejercicio 3
# ---------------------------------------------------------------------------


def exercise_3_page() -> None:
    section_intro(
        "Ejercicio 3 · Distribuciones por composición",
        "Algoritmos para los tres incisos obtenidos directamente a partir del método del ejercicio 2.",
    )
    exercise_statement(
        r"Utilizando el resultado del Ejercicio 2, proporcione algoritmos para generar variables "
        r"aleatorias a partir de las siguientes distribuciones: "
        r"(a) $F(x)=(x+x^3+x^5)/3$, $0\le x\le1$; "
        r"(b) $F(x)=(1-e^{-2x}+2x)/3$ para $0<x<1$ y "
        r"$F(x)=(3-e^{-2x})/3$ para $1<x<\infty$; "
        r"(c) $F(x)=\sum_{i=1}^{n}\alpha_i x^i$, $0\le x\le1$, donde "
        r"$\alpha_i\ge0$ y $\sum_{i=1}^{n}\alpha_i=1$."
    )
    case = st.radio(
        "Selecciona el inciso",
        ["a", "b", "c"],
        horizontal=True,
        format_func=lambda item: f"Inciso ({item})",
    )
    if case == "a":
        st.latex(r"F(x)=\frac{x+x^3+x^5}{3},\qquad 0\le x\le1")
        st.markdown("Se elige con probabilidad $1/3$ una de las CDF $x$, $x^3$ o $x^5$.")
        st.latex(r"J\in\{1,3,5\},\qquad X=U^{1/J}")
    elif case == "b":
        st.latex(
            r"F(x)=\begin{cases}(1-e^{-2x}+2x)/3,&0<x<1,\\"
            r"(3-e^{-2x})/3,&1\le x<\infty.\end{cases}"
        )
        st.markdown(
            "Es una mezcla de una exponencial de tasa 2 con peso $1/3$ y una uniforme "
            "en $(0,1)$ con peso $2/3$."
        )
        st.latex(r"X=\begin{cases}-\ln(1-U)/2,&P=1/3,\\U,&P=2/3.\end{cases}")
    else:
        st.latex(r"F(x)=\sum_{i=1}^{n}\alpha_i x^i,\qquad \alpha_i\ge0,\quad\sum_i\alpha_i=1")
        st.markdown("Se selecciona $I=i$ con probabilidad $\alpha_i$ y después se usa $X=U^{1/i}$.")

    with st.form("exercise_3_form"):
        col1, col2, col3 = st.columns(3)
        alpha_text = col1.text_input(
            "Pesos alpha_i para el inciso (c)",
            "0.10, 0.20, 0.30, 0.40",
            disabled=case != "c",
        )
        sample_size = col2.number_input("Muestras", 100, 200_000, 10_000, 100, key="ex3_n")
        seed = col3.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex3_seed")
        submitted = st.form_submit_button(f"Generar distribución del inciso ({case})", type="primary", width="stretch")
    if submitted:
        try:
            weights = _parse_weights(alpha_text) if case == "c" else None
            st.session_state["ex3_result"] = simulate_composition(case, int(sample_size), int(seed), weights)
            st.session_state["ex3_case"] = case
        except SimulationError as exc:
            st.error(str(exc))
            st.session_state.pop("ex3_result", None)
    if "ex3_result" not in st.session_state or st.session_state.get("ex3_case") != case:
        return
    result: CompositionResult = st.session_state["ex3_result"]
    cdf_tab, histogram_tab, table_tab = st.tabs(["Comparación de CDF", "Distribución generada", "Todas las muestras"])
    with cdf_tab:
        figure = px.line(result.comparison, x="x", y=["F teórica", "F empírica"], title=f"Inciso ({case}): CDF teórica frente a simulada")
        st.plotly_chart(figure)
    with histogram_tab:
        figure = px.histogram(result.samples, x="X generada", color="Distribución elegida", nbins=55, title="Valores producidos por cada componente")
        st.plotly_chart(figure)
    with table_tab:
        st.dataframe(result.samples, width="stretch", hide_index=True, height=520)
        download_table(result.samples, f"ejercicio_3_{case}_composicion.csv", f"download_ex3_{case}")


# ---------------------------------------------------------------------------
# Ejercicio 4
# ---------------------------------------------------------------------------


def exercise_4_page() -> None:
    section_intro(
        "Ejercicio 4 · Cartera de seguros",
        "Estimación de la probabilidad de que las reclamaciones mensuales de 1,000 asegurados excedan $50,000.",
    )
    exercise_statement(
        "Una compañía de seguros contra siniestros tiene 1,000 asegurados, cada uno de los cuales "
        "presentará una reclamación en el próximo mes de manera independiente con probabilidad 0.05. "
        "Suponiendo que los montos de las reclamaciones son variables aleatorias exponenciales "
        "independientes con media \\$800, utilice simulación para estimar la probabilidad de que la "
        "suma de estas reclamaciones exceda \\$50,000."
    )
    st.latex(r"N\sim\mathrm{Binomial}(1000,0.05),\qquad Y_i\sim\mathrm{Exp}(1/800)")
    st.latex(r"S=\sum_{i=1}^{N}Y_i,\qquad P(S>50{,}000)")
    with st.expander("Fundamento y referencia matemática", expanded=True):
        st.markdown(
            "Condicionado a $N=n$, la suma de $n$ exponenciales independientes es "
            "Gamma con forma $n$ y escala 800. Esto permite generar el monto agregado "
            "eficientemente y calcular una referencia de comparación."
        )
        st.latex(
            r"P(S>c)=\sum_{n=1}^{1000}P(N=n)P(\mathrm{Gamma}(n,800)>c)"
        )
        st.latex(r"E[S]=1000(0.05)(800)=40{,}000")

    with st.form("exercise_4_form"):
        col1, col2 = st.columns(2)
        replications = col1.number_input("Meses simulados", 1_000, 500_000, 50_000, 1_000)
        seed = col2.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex4_seed")
        submitted = st.form_submit_button("Simular cartera", type="primary", width="stretch")
    if submitted:
        st.session_state["ex4_result"] = simulate_insurance_claims(int(seed), int(replications))
    if "ex4_result" not in st.session_state:
        return
    result: InsuranceResult = st.session_state["ex4_result"]
    summary = result.summary
    cols = st.columns(5)
    cols[0].metric("Probabilidad estimada", f"{summary.estimate:.4%}")
    cols[1].metric("Referencia exacta", f"{result.exact_probability:.4%}")
    cols[2].metric("Error absoluto", format_number(abs(summary.estimate - result.exact_probability), 7))
    cols[3].metric("IC aproximado 95 %", f"[{summary.ci_low:.3%}, {summary.ci_high:.3%}]")
    cols[4].metric("Pérdida esperada", f"${result.expected_aggregate:,.0f}")
    distribution_tab, convergence_tab, first_tab, table_tab = st.tabs(
        ["Montos agregados", "Convergencia", "Primera réplica", "Todos los meses"]
    )
    with distribution_tab:
        figure = px.histogram(result.months, x="Monto agregado", nbins=70, title="Distribución simulada del monto mensual", color_discrete_sequence=["#08783f"])
        figure.add_vline(x=50_000, line_dash="dash", line_color="#b64747", annotation_text="Umbral $50,000")
        st.plotly_chart(figure)
    with convergence_tab:
        shown = result.months.iloc[:: max(1, len(result.months) // 3000)]
        figure = px.line(shown, x="Mes simulado", y="Probabilidad acumulada", title="Convergencia de P(S > 50,000)")
        figure.add_hline(y=result.exact_probability, line_dash="dash", line_color="#d99000", annotation_text="Referencia")
        st.plotly_chart(figure)
    with first_tab:
        st.caption("Montos individuales de la primera réplica; su suma coincide con el monto agregado mostrado para ese mes.")
        st.dataframe(result.first_month_claims, width="stretch", hide_index=True, height=500)
    with table_tab:
        st.dataframe(result.months, width="stretch", hide_index=True, height=520)
        download_table(result.months, "ejercicio_4_cartera_seguros.csv", "download_ex4")


# ---------------------------------------------------------------------------
# Ejercicio 5
# ---------------------------------------------------------------------------


def exercise_5_page() -> None:
    section_intro(
        "Ejercicio 5 · Normal por rechazo exponencial",
        "Implementación literal del método del Ejemplo 5f usando exponenciales independientes de tasa 1.",
    )
    exercise_statement(
        "Escriba un programa que genere variables aleatorias normales utilizando el método del "
        "Ejemplo 5f: método de rechazo con una distribución exponencial de tasa 1."
    )
    st.markdown("Para generar el valor absoluto de una normal estándar se usa una exponencial como densidad auxiliar.")
    st.latex(r"Y_1,Y_2\sim\mathrm{Exp}(1)")
    st.latex(r"\text{Aceptar }Y_1\quad\Longleftrightarrow\quad Y_2>\frac{(Y_1-1)^2}{2}")
    st.markdown("Una vez aceptado, un uniforme adicional asigna signo positivo o negativo con igual probabilidad.")
    st.latex(r"P(\mathrm{aceptar})=\sqrt{\frac{\pi}{2e}}\approx0.76017")
    st.markdown(
        "El residual aceptado es una exponencial independiente y se reutiliza como $Y_1$ de la "
        "siguiente normal, tal como indica el material de apoyo."
    )
    st.latex(
        r"E[\text{exponenciales por normal}]=2\sqrt{\frac{2e}{\pi}}-1\approx1.631,"
        r"\qquad E[\text{cuadrados por normal}]=\sqrt{\frac{2e}{\pi}}\approx1.315"
    )
    with st.expander("Pseudocódigo", expanded=False):
        st.code(
            "Repetir:\n"
            "    generar Y1, Y2 exponenciales de tasa 1\n"
            "    si Y2 > (Y1-1)^2/2:\n"
            "        guardar Y2-(Y1-1)^2/2 como Y1 de la próxima normal\n"
            "        generar U\n"
            "        devolver Y1 si U <= 1/2; en otro caso devolver -Y1",
            language="text",
        )
    with st.form("exercise_5_form"):
        col1, col2 = st.columns(2)
        sample_size = col1.number_input("Normales requeridas", 100, 200_000, 10_000, 100)
        seed = col2.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex5_seed")
        submitted = st.form_submit_button("Generar normales", type="primary", width="stretch")
    if submitted:
        st.session_state["ex5_result"] = generate_normal_exponential_rejection(int(seed), int(sample_size))
    if "ex5_result" not in st.session_state:
        return
    result: NormalRejectionResult = st.session_state["ex5_result"]
    cols = st.columns(5)
    cols[0].metric("Media simulada", format_number(result.mean))
    cols[1].metric("Varianza simulada", format_number(result.variance))
    cols[2].metric("Aceptación empírica", f"{result.acceptance_rate:.2%}")
    cols[3].metric("Aceptación teórica", f"{result.theoretical_acceptance:.2%}")
    cols[4].metric("Intentos", f"{len(result.attempts):,}")
    efficiency_cols = st.columns(2)
    efficiency_cols[0].metric(
        "Exponenciales por normal",
        format_number(result.exponentials_generated / len(result.samples), 4),
        help="Referencia asintótica aproximada: 1.631.",
    )
    efficiency_cols[1].metric(
        "Cuadrados por normal",
        format_number(result.squares_computed / len(result.samples), 4),
        help="Referencia asintótica aproximada: 1.315.",
    )
    dist_tab, sample_tab, attempts_tab = st.tabs(["Comparación normal", "Valores aceptados", "Todos los intentos"])
    with dist_tab:
        st.plotly_chart(
            normal_histogram(
                result.samples["Z"].to_numpy(),
                "Normal generada por rechazo exponencial",
            )
        )
    with sample_tab:
        st.dataframe(result.samples, width="stretch", hide_index=True, height=520)
        download_table(result.samples, "ejercicio_5_normales.csv", "download_ex5_samples")
    with attempts_tab:
        st.dataframe(result.attempts, width="stretch", hide_index=True, height=520)
        download_table(result.attempts, "ejercicio_5_intentos.csv", "download_ex5_attempts")


# ---------------------------------------------------------------------------
# Ejercicio 6
# ---------------------------------------------------------------------------


def exercise_6_page() -> None:
    section_intro(
        "Ejercicio 6 · Proceso de Poisson homogéneo",
        "Generación de todos los eventos ocurridos durante las primeras T unidades de tiempo con tasa lambda.",
    )
    exercise_statement(
        r"Escriba un programa que genere las primeras $T$ unidades de tiempo de un proceso de "
        r"Poisson con tasa $\lambda$."
    )
    st.markdown("Los tiempos entre llegadas son exponenciales independientes y sus sumas producen los tiempos de evento.")
    st.latex(r"E_i\sim\mathrm{Exp}(\lambda),\qquad S_n=\sum_{i=1}^{n}E_i")
    st.latex(r"N(T)=\max\{n:S_n\le T\}\sim\mathrm{Poisson}(\lambda T)")
    with st.form("exercise_6_form"):
        col1, col2, col3 = st.columns(3)
        rate = col1.number_input("Tasa lambda", min_value=0.01, max_value=100.0, value=2.0, step=0.1)
        horizon = col2.number_input("Horizonte T", min_value=0.1, max_value=1_000.0, value=10.0, step=0.5)
        seed = col3.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex6_seed")
        submitted = st.form_submit_button("Generar proceso homogéneo", type="primary", width="stretch")
    if submitted:
        try:
            st.session_state["ex6_result"] = simulate_homogeneous_poisson(float(rate), float(horizon), int(seed))
        except SimulationError as exc:
            st.error(str(exc))
            st.session_state.pop("ex6_result", None)
    if "ex6_result" not in st.session_state:
        return
    result: PoissonProcessResult = st.session_state["ex6_result"]
    cols = st.columns(4)
    cols[0].metric("Eventos observados", str(result.count))
    cols[1].metric("Eventos esperados", format_number(result.expected_count, 3))
    cols[2].metric("Último evento", "Ninguno" if result.count == 0 else format_number(float(result.path.iloc[-2]["Tiempo"]), 5))
    cols[3].metric("Uniformes generados", str(len(result.events)))
    process_tab, arrivals_tab = st.tabs(["Trayectoria N(t)", "Tabla de generación"])
    with process_tab:
        figure = px.line(result.path, x="Tiempo", y="N(t)", line_shape="hv", markers=True, title="Función de conteo del proceso de Poisson")
        st.plotly_chart(figure)
    with arrivals_tab:
        st.dataframe(result.events, width="stretch", hide_index=True, height=520)
        download_table(result.events, "ejercicio_6_poisson_homogeneo.csv", "download_ex6")


# ---------------------------------------------------------------------------
# Ejercicio 7
# ---------------------------------------------------------------------------


def _nhpp_event_figure(result: NHPPComparisonResult) -> go.Figure:
    grid = np.linspace(0, result.horizon, 500)
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=grid, y=nhpp_intensity(grid), name="lambda(t)", line=dict(color="#08783f", width=3)))
    figure.add_trace(go.Scatter(x=grid, y=np.full_like(grid, 7.0), name="Cota global M=7", line=dict(color="#b64747", dash="dash")))
    if not result.global_method.events.empty:
        figure.add_trace(go.Scatter(x=result.global_method.events["Tiempo"], y=np.zeros(result.global_method.count), mode="markers", name="Eventos: método global", marker=dict(symbol="line-ns-open", size=14, color="#d99000")))
    if not result.improved_method.events.empty:
        figure.add_trace(go.Scatter(x=result.improved_method.events["Tiempo"], y=np.full(result.improved_method.count, 0.25), mode="markers", name="Eventos: método mejorado", marker=dict(symbol="line-ns-open", size=14, color="#064d2d")))
    figure.update_layout(title="Intensidad y eventos aceptados", xaxis_title="t", yaxis_title="Tasa")
    return figure


def exercise_7_page() -> None:
    section_intro(
        "Ejercicio 7 · Poisson no homogéneo",
        "Adelgazamiento durante las primeras 10 unidades y mejora mediante cotas locales.",
    )
    exercise_statement(
        r"(a) Escriba un programa que utilice el algoritmo de adelgazamiento (thinning) para generar "
        r"las primeras 10 unidades de tiempo de un proceso de Poisson no homogéneo con función de "
        r"intensidad $\lambda(t)=3+4/(t+1)$. "
        r"(b) Proponga una manera de mejorar el algoritmo de adelgazamiento para este ejemplo."
    )
    st.latex(r"\lambda(t)=3+\frac{4}{t+1},\qquad 0\le t\le10")
    theory_tab, simulation_tab = st.tabs(["Incisos (a) y (b)", "Comparación por simulación"])
    with theory_tab:
        st.subheader("(a) Adelgazamiento con cota global")
        st.markdown("Como la intensidad es decreciente, su máximo ocurre en $t=0$ y vale $M=7$.")
        st.code(
            "t = 0\n"
            "mientras t <= 10:\n"
            "    t = t + Exponencial(tasa=7)\n"
            "    si t <= 10 y U <= lambda(t)/7: aceptar el evento t",
            language="text",
        )
        st.latex(r"E[N(10)]=\int_0^{10}\lambda(t)\,dt=30+4\ln(11)\approx39.5916")
        st.subheader("(b) Mejora propuesta")
        st.markdown(
            r"Usar $M=7$ en todo el intervalo genera propuestas innecesarias porque la intensidad disminuye. "
            r"Se divide $[0,10]$ en intervalos unitarios y, en $[k,k+1)$, se utiliza la cota local "
            r"$M_k=\lambda(k)$. La cota sigue siendo válida y queda mucho más cerca de la intensidad real."
        )
        st.latex(r"M_k=3+\frac{4}{k+1},\qquad k=0,1,\ldots,9")
        st.latex(
            r"E[\text{propuestas globales}]=7(10)=70,\qquad "
            r"E[\text{propuestas locales}]=\sum_{k=0}^{9}M_k\approx41.7159"
        )
        st.caption(
            "Las dos ejecuciones usan flujos aleatorios independientes derivados de la misma semilla; "
            "por eso no deben producir exactamente los mismos eventos. La mejora se evalúa por la reducción de propuestas."
        )
    with simulation_tab:
        with st.form("exercise_7_form"):
            seed = st.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex7_seed")
            st.caption("El horizonte T=10 y la intensidad permanecen fijos porque los determina el PDF.")
            submitted = st.form_submit_button("Comparar ambos algoritmos", type="primary", width="stretch")
        if submitted:
            st.session_state["ex7_result"] = simulate_nhpp_comparison(int(seed))
        if "ex7_result" not in st.session_state:
            return
        result: NHPPComparisonResult = st.session_state["ex7_result"]
        cols = st.columns(5)
        cols[0].metric("E[N(10)]", format_number(result.expected_count, 4))
        cols[1].metric("Eventos global", str(result.global_method.count))
        cols[2].metric("Propuestas global", str(result.global_method.proposal_count))
        cols[3].metric("Eventos mejorado", str(result.improved_method.count))
        cols[4].metric("Propuestas mejorado", str(result.improved_method.proposal_count))
        chart_tab, global_tab, improved_tab = st.tabs(["Intensidad y eventos", "Cota global", "Cotas locales"])
        with chart_tab:
            st.plotly_chart(_nhpp_event_figure(result))
        with global_tab:
            st.metric("Tasa de aceptación", f"{result.global_method.acceptance_rate:.2%}")
            st.dataframe(result.global_method.proposals, width="stretch", hide_index=True, height=500)
            download_table(result.global_method.proposals, "ejercicio_7_adelgazamiento_global.csv", "download_ex7_global")
        with improved_tab:
            st.metric("Tasa de aceptación", f"{result.improved_method.acceptance_rate:.2%}")
            st.dataframe(result.improved_method.proposals, width="stretch", hide_index=True, height=500)
            download_table(result.improved_method.proposals, "ejercicio_7_adelgazamiento_mejorado.csv", "download_ex7_improved")


# ---------------------------------------------------------------------------
# Ejercicio 8
# ---------------------------------------------------------------------------


def exercise_8_page() -> None:
    section_intro(
        "Ejercicio 8 · Proceso de Poisson bidimensional",
        "Generación y gráfica de los puntos de un proceso espacial dentro de un círculo.",
    )
    exercise_statement(
        r"Escriba un programa para generar los puntos de un proceso de Poisson bidimensional dentro "
        r"de un círculo de radio $R$, y ejecute el programa para $\lambda=1$ y $R=5$. "
        r"Grafique los puntos obtenidos."
    )
    st.markdown(r"El enunciado requiere ejecutar el algoritmo con $\lambda=1$ y $R=5$.")
    st.latex(r"N\sim\mathrm{Poisson}(\lambda\pi R^2)")
    st.latex(r"r=R\sqrt{U_1},\qquad\theta=2\pi U_2,\qquad(x,y)=(r\cos\theta,r\sin\theta)")
    theory_card(
        "<strong>Detalle importante.</strong> El radio no es uniforme. Se usa r=R√U porque el área "
        "crece proporcionalmente a r²; omitir la raíz concentraría puntos cerca del centro."
    )
    with st.form("exercise_8_form"):
        seed = st.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex8_seed")
        st.caption("Parámetros fijados por el PDF: intensidad lambda=1 y radio R=5.")
        submitted = st.form_submit_button("Generar puntos en el círculo", type="primary", width="stretch")
    if submitted:
        st.session_state["ex8_result"] = simulate_spatial_poisson(1.0, 5.0, int(seed))
    if "ex8_result" not in st.session_state:
        return
    result: SpatialPoissonResult = st.session_state["ex8_result"]
    cols = st.columns(4)
    cols[0].metric("Puntos generados", str(result.count))
    cols[1].metric("Cantidad esperada", format_number(result.expected_count, 4))
    cols[2].metric("U para N", format_number(result.count_uniform, 8))
    cols[3].metric("Mayor radio", "0" if result.points.empty else format_number(float(result.points["Radio r"].max()), 5))
    plot_tab, table_tab = st.tabs(["Gráfica espacial", "Coordenadas y uniformes"])
    with plot_tab:
        st.plotly_chart(
            spatial_figure(result, "Proceso de Poisson espacial: lambda=1, R=5")
        )
    with table_tab:
        st.dataframe(result.points, width="stretch", hide_index=True, height=520)
        download_table(result.points, "ejercicio_8_poisson_bidimensional.csv", "download_ex8")


# ---------------------------------------------------------------------------
# Ejercicio 9
# ---------------------------------------------------------------------------


def exercise_9_page() -> None:
    section_intro(
        "Ejercicio 9 · Método polar de Marsaglia",
        "Explicación, utilidad, ejemplo numérico y verificación programada del generador normal polar.",
    )
    exercise_statement(
        r"Explique el método polar para generar variables aleatorias normales. Su explicación debe "
        r"incluir: (a) en qué consiste el método, con idea general y algoritmo paso a paso; "
        r"(b) para qué sirve, qué problema resuelve y por qué es preferible frente al uso directo de "
        r"las transformaciones de Box–Muller; y (c) un ejemplo numérico en el que se elijan $U_1$ y "
        r"$U_2$ y se aplique el algoritmo hasta obtener el par de normales $X,Y$, seleccionando otro "
        r"par si el primero cae fuera del círculo unitario."
    )
    a_tab, b_tab, c_tab, simulation_tab = st.tabs(["(a) Método", "(b) Utilidad", "(c) Ejemplo", "Demostración"])
    with a_tab:
        st.markdown(
            "Se generan dos uniformes, se trasladan al cuadrado $(-1,1)^2$ y se conservan únicamente "
            "los pares dentro del círculo unitario. Un mismo par aceptado produce dos normales estándar independientes."
        )
        st.latex(r"V_1=2U_1-1,\qquad V_2=2U_2-1,\qquad S=V_1^2+V_2^2")
        st.latex(r"0<S<1:\qquad X=V_1\sqrt{\frac{-2\ln S}{S}},\quad Y=V_2\sqrt{\frac{-2\ln S}{S}}")
        st.code(
            "Repetir:\n"
            "    generar U1, U2\n"
            "    V1=2U1-1, V2=2U2-1, S=V1^2+V2^2\n"
            "hasta que 0 < S < 1\n"
            "factor=sqrt(-2*log(S)/S)\n"
            "devolver X=V1*factor, Y=V2*factor",
            language="text",
        )
    with b_tab:
        st.markdown(
            "Sirve para generar pares de variables normales estándar independientes. Frente a la "
            "transformación directa de Box–Muller evita evaluar seno y coseno, operaciones que históricamente "
            "son más costosas. A cambio, rechaza los puntos que caen fuera del círculo. En hardware moderno "
            "la ventaja exacta depende de la implementación, pero esta es la razón algorítmica clásica."
        )
        st.latex(r"P(\mathrm{aceptar})=\frac{\text{área del círculo}}{\text{área del cuadrado}}=\frac{\pi}{4}\approx0.7854")
    with c_tab:
        st.markdown("Ejemplo propuesto: $U_1=0.70$ y $U_2=0.40$.")
        try:
            v1, v2, s, x, y = polar_transform(0.70, 0.40)
            example = pd.DataFrame(
                {
                    "Paso": ["Transformar U1", "Transformar U2", "Calcular S", "Normal X", "Normal Y"],
                    "Cálculo": ["2(0.70)-1", "2(0.40)-1", "V1²+V2²", "V1·sqrt(-2 ln(S)/S)", "V2·sqrt(-2 ln(S)/S)"],
                    "Resultado": [v1, v2, s, x, y],
                }
            )
            st.dataframe(example, width="stretch", hide_index=True)
            st.success(f"Como S={s:.4f} pertenece a (0,1), se acepta el par: X={x:.6f}, Y={y:.6f}.")
        except SimulationError as exc:
            st.error(str(exc))
    with simulation_tab:
        with st.form("exercise_9_form"):
            col1, col2 = st.columns(2)
            sample_size = col1.number_input("Normales requeridas", 100, 200_000, 10_000, 100, key="ex9_n")
            seed = col2.number_input("Semilla", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex9_seed")
            submitted = st.form_submit_button("Generar con método polar", type="primary", width="stretch")
        if submitted:
            st.session_state["ex9_result"] = generate_normal_polar(int(seed), int(sample_size))
        if "ex9_result" not in st.session_state:
            return
        result: PolarNormalResult = st.session_state["ex9_result"]
        cols = st.columns(4)
        cols[0].metric("Media", format_number(result.mean))
        cols[1].metric("Varianza", format_number(result.variance))
        cols[2].metric("Aceptación empírica", f"{result.acceptance_rate:.2%}")
        cols[3].metric("Aceptación teórica", f"{math.pi/4:.2%}")
        dist_tab, pairs_tab, attempts_tab = st.tabs(["Distribución", "Pares aceptados", "Intentos"])
        with dist_tab:
            st.plotly_chart(
                normal_histogram(
                    result.values,
                    "Normales obtenidas con el método polar",
                )
            )
        with pairs_tab:
            st.dataframe(result.pairs, width="stretch", hide_index=True, height=500)
            download_table(result.pairs, "ejercicio_9_pares_polares.csv", "download_ex9_pairs")
        with attempts_tab:
            st.dataframe(result.attempts, width="stretch", hide_index=True, height=500)


# ---------------------------------------------------------------------------
# Ejercicio 10
# ---------------------------------------------------------------------------


def exercise_10_page() -> None:
    section_intro(
        "Ejercicio 10 · Proceso de Poisson bidimensional",
        "Definición formal, aplicaciones, algoritmo y ejemplo numérico para lambda=1 y R=2.",
    )
    exercise_statement(
        r"Explique el proceso de Poisson bidimensional y el algoritmo para simularlo dentro de una "
        r"región circular. Incluya: (a) definición formal y algoritmo paso a paso; "
        r"(b) para qué sirve, qué fenómenos modela y por qué es útil simularlo; y "
        r"(c) un ejemplo numérico para $\lambda=1$ y $R=2$, eligiendo los números aleatorios "
        r"necesarios y aplicando el algoritmo hasta obtener las coordenadas polares de los puntos."
    )
    a_tab, b_tab, c_tab = st.tabs(["(a) Definición y algoritmo", "(b) Aplicaciones", "(c) Ejemplo numérico"])
    with a_tab:
        st.markdown(
            r"Un proceso de Poisson bidimensional homogéneo con intensidad $\lambda$ asigna a cada "
            r"región medible $A$ un conteo aleatorio $N(A)$ con las siguientes propiedades:"
        )
        st.latex(r"N(A)\sim\mathrm{Poisson}(\lambda|A|)")
        st.markdown(
            "Los conteos de regiones disjuntas son independientes. Condicionado a $N(A)=n$, los $n$ "
            "puntos son independientes y uniformes dentro de $A$. Para un círculo de radio $R$:"
        )
        st.code(
            "1. Generar N ~ Poisson(lambda*pi*R^2).\n"
            "2. Para cada punto generar U_r y U_theta.\n"
            "3. r=R*sqrt(U_r), theta=2*pi*U_theta.\n"
            "4. x=r*cos(theta), y=r*sin(theta).",
            language="text",
        )
    with b_tab:
        st.markdown(
            "Este proceso modela ubicaciones aleatorias sin interacción espacial: accidentes en una zona, "
            "defectos sobre una superficie, árboles en una región, impactos, antenas, microorganismos o "
            "eventos epidemiológicos. Simularlo permite estudiar cobertura, distancias, concentración y "
            "riesgo cuando una solución analítica resulta difícil."
        )
    with c_tab:
        st.latex(r"\lambda=1,\qquad R=2,\qquad E[N]=\lambda\pi R^2=4\pi\approx12.5664")
        with st.form("exercise_10_form"):
            seed = st.number_input("Semilla del ejemplo", 0, 2_147_483_647, DEFAULT_SEED, 1, key="ex10_seed")
            submitted = st.form_submit_button("Construir ejemplo numérico", type="primary", width="stretch")
        if submitted:
            st.session_state["ex10_result"] = simulate_spatial_poisson(1.0, 2.0, int(seed))
        if "ex10_result" not in st.session_state:
            st.info("Ejecuta el ejemplo para obtener el uniforme del conteo y las coordenadas polares paso a paso.")
            return
        result: SpatialPoissonResult = st.session_state["ex10_result"]
        st.markdown(
            f'<div class="result-card"><strong>Resultado del conteo.</strong> Con U={result.count_uniform:.8f}, '
            f'la inversión de Poisson con media 4π produjo N={result.count} puntos.</div>',
            unsafe_allow_html=True,
        )
        plot_tab, table_tab = st.tabs(["Puntos del ejemplo", "Cálculo polar completo"])
        with plot_tab:
            st.plotly_chart(
                spatial_figure(result, "Ejemplo numérico: lambda=1, R=2")
            )
        with table_tab:
            st.dataframe(result.points, width="stretch", hide_index=True, height=500)
            download_table(result.points, "ejercicio_10_ejemplo_numerico.csv", "download_ex10")


PAGE_FUNCTIONS = {
    NAVIGATION[0]: exercise_1_page,
    NAVIGATION[1]: exercise_2_page,
    NAVIGATION[2]: exercise_3_page,
    NAVIGATION[3]: exercise_4_page,
    NAVIGATION[4]: exercise_5_page,
    NAVIGATION[5]: exercise_6_page,
    NAVIGATION[6]: exercise_7_page,
    NAVIGATION[7]: exercise_8_page,
    NAVIGATION[8]: exercise_9_page,
    NAVIGATION[9]: exercise_10_page,
}


def sidebar() -> str:
    with st.sidebar:
        st.markdown("### Navegación")
        selected = st.selectbox("Ejercicio", NAVIGATION, label_visibility="collapsed")
        st.divider()
        st.markdown("**Configuración de reproducibilidad**")
        st.caption(
            "La semilla 22193 corresponde a mi carné. Puede cambiarse en cada ejercicio para obtener otra trayectoria."
        )
        st.markdown(f"[Repositorio del proyecto]({REPOSITORY_URL})")
        st.divider()
        st.caption("CC2017 · Sección 30 · Ciclo 2, 2026")
    return selected


def main() -> None:
    selected = sidebar()
    st.markdown(ACADEMIC_HEADER, unsafe_allow_html=True)
    PAGE_FUNCTIONS[selected]()
    st.divider()
    st.caption(
        "Los resultados Monte Carlo son estimaciones. Las tablas conservan los números aleatorios para que cada procedimiento pueda auditarse."
    )


if __name__ == "__main__":
    main()
