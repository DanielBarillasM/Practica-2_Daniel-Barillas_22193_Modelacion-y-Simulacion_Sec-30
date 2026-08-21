"""Genera una versión PDF del informe sin depender de Microsoft Word.

El documento usa los mismos resultados JSON que el README y el DOCX. Esta ruta
evita diálogos o bloqueos de automatización de Office y mantiene reproducibles
ambos formatos de entrega.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "data" / "resultados_referencia.json"
OUTPUT_PATH = ROOT / "docs" / "informe" / "Informe_Practica_2_Daniel_Barillas_22193.pdf"
REPOSITORY_URL = (
    "https://github.com/DanielBarillasM/"
    "Practica-2_Daniel-Barillas_22193_Modelacion-y-Simulacion_Sec-30"
)

GREEN = colors.HexColor("#08783F")
DARK_GREEN = colors.HexColor("#064D2D")
SOFT_GREEN = colors.HexColor("#EAF5EE")
GRAY = colors.HexColor("#5A675F")


def register_fonts() -> tuple[str, str]:
    """Usa Arial cuando está disponible para conservar acentos y símbolos."""

    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Academic", regular))
        pdfmetrics.registerFont(TTFont("Academic-Bold", bold))
        return "Academic", "Academic-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def header_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.75 * inch, 0.45 * inch, "UVG · CC2017 · Modelación y Simulación")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Página {document.page}")
    canvas.restoreState()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AcademicTitle", parent=base["Title"], fontName=FONT_BOLD,
            fontSize=24, leading=29, textColor=DARK_GREEN, alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "subtitle": ParagraphStyle(
            "AcademicSubtitle", parent=base["Heading2"], fontName=FONT_BOLD,
            fontSize=16, leading=20, textColor=GREEN, alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "AcademicH1", parent=base["Heading1"], fontName=FONT_BOLD,
            fontSize=16, leading=20, textColor=DARK_GREEN, spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "AcademicH2", parent=base["Heading2"], fontName=FONT_BOLD,
            fontSize=12.5, leading=16, textColor=GREEN, spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "AcademicBody", parent=base["BodyText"], fontName=FONT,
            fontSize=9.6, leading=14, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "statement": ParagraphStyle(
            "AcademicStatement", parent=base["BodyText"], fontName=FONT,
            fontSize=9.3, leading=13.5, leftIndent=10, rightIndent=10,
            borderColor=GREEN, borderWidth=1, borderPadding=8,
            backColor=SOFT_GREEN, spaceAfter=8,
        ),
        "equation": ParagraphStyle(
            "AcademicEquation", parent=base["BodyText"], fontName=FONT,
            fontSize=10, leading=14, alignment=TA_CENTER, textColor=DARK_GREEN,
            spaceAfter=7,
        ),
        "center": ParagraphStyle(
            "AcademicCenter", parent=base["BodyText"], fontName=FONT,
            fontSize=10, leading=15, alignment=TA_CENTER, spaceAfter=5,
        ),
    }


EXERCISES = [
    (
        "Ejercicio 1 — Exponencial condicionada",
        "Sea X exponencial con media 1. Genere eficientemente 1,000 valores condicionados a X&lt;0.05, estime E[X | X&lt;0.05] y determine el valor exacto.",
        "Se aplica transformación inversa: X = -ln(1-U(1-e^(-0.05))). La media exacta es 0.02479167535.",
    ),
    (
        "Ejercicio 2 — Método de composición",
        "Explique cómo generar una variable con CDF F(x)=sum p_i F_i(x), con pesos no negativos que suman 1.",
        "Se genera primero I con P(I=i)=p_i y después X condicionado a I=i usando F_i. La probabilidad total demuestra la mezcla.",
    ),
    (
        "Ejercicio 3 — Aplicaciones de composición",
        "Utilice el Ejercicio 2 para proporcionar algoritmos para las distribuciones de los incisos (a), (b) y (c).",
        "Las CDF potencia usan X=U^(1/i). El inciso (b) mezcla una exponencial de tasa 2 con peso 1/3 y una uniforme(0,1) con peso 2/3.",
    ),
    (
        "Ejercicio 4 — Cartera de seguros",
        "Con 1,000 asegurados, probabilidad de reclamación 0.05 y montos exponenciales de media $800, estime P(S&gt;$50,000).",
        "N es binomial y, condicionado a N=n, S es Gamma(n,800). La referencia es 0.1070977013.",
    ),
    (
        "Ejercicio 5 — Normal por rechazo exponencial",
        "Genere variables normales con el método de rechazo exponencial de tasa 1 del Ejemplo 5f.",
        "Se acepta Y1 si Y2&gt;(Y1-1)^2/2. El residual independiente se recicla y se obtienen aproximadamente 1.64 exponenciales y 1.32 cuadrados por normal.",
    ),
    (
        "Ejercicio 6 — Poisson homogéneo",
        "Genere las primeras T unidades de tiempo de un proceso de Poisson con tasa lambda.",
        "Se acumulan tiempos entre llegadas Exp(lambda) hasta superar T; N(T) tiene distribución Poisson(lambda*T).",
    ),
    (
        "Ejercicio 7 — Poisson no homogéneo",
        "Genere por adelgazamiento el proceso con lambda(t)=3+4/(t+1) en [0,10] y proponga una mejora.",
        "El método base usa M=7. La mejora usa cotas locales M_k=lambda(k), reduciendo las propuestas esperadas de 70 a 41.7159.",
    ),
    (
        "Ejercicio 8 — Poisson bidimensional",
        "Genere y grafique los puntos dentro de un círculo para lambda=1 y R=5.",
        "N es Poisson(lambda*pi*R^2); para uniformidad espacial se usa r=R*sqrt(U) y theta=2*pi*V.",
    ),
    (
        "Ejercicio 9 — Método polar",
        "Explique el método polar, su utilidad frente a Box-Muller y desarrolle un ejemplo numérico.",
        "Se aceptan pares con S=V1^2+V2^2 en (0,1) y se multiplica por sqrt(-2 ln(S)/S). La aceptación es pi/4.",
    ),
    (
        "Ejercicio 10 — Poisson bidimensional: teoría",
        "Defina el proceso, explique sus aplicaciones y desarrolle un ejemplo para lambda=1 y R=2.",
        "Para toda región A, N(A) es Poisson(lambda*|A|); los conteos de regiones disjuntas son independientes.",
    ),
]


def build_pdf() -> None:
    result = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    style = styles()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=letter, rightMargin=0.7 * inch,
        leftMargin=0.7 * inch, topMargin=0.65 * inch, bottomMargin=0.68 * inch,
        title="Práctica 2 — Generación de Variables Aleatorias Continuas",
        author="Pablo Daniel Barillas Moreno",
    )
    story = [
        Spacer(1, 0.35 * inch),
        Paragraph("UNIVERSIDAD DEL VALLE DE GUATEMALA", style["subtitle"]),
        Paragraph("Práctica 2", style["title"]),
        Paragraph("Generación de Variables Aleatorias Continuas", style["subtitle"]),
        Spacer(1, 0.15 * inch),
        Paragraph("CC2017 — Modelación y Simulación", style["center"]),
        Paragraph("Ciclo 2, 2026 · Sección 30", style["center"]),
        Paragraph("Pablo Daniel Barillas Moreno · Carné 22193", style["center"]),
        Paragraph("Semilla reproducible: 22193", style["center"]),
        Spacer(1, 0.18 * inch),
        Paragraph(f'<link href="{REPOSITORY_URL}" color="#08783F">{REPOSITORY_URL}</link>', style["center"]),
        PageBreak(),
        Paragraph("1. Introducción", style["h1"]),
        Paragraph(
            "Este informe presenta la teoría, los algoritmos y los resultados reproducibles de los "
            "diez ejercicios. Cada enunciado se muestra también dentro de su página de Streamlit.",
            style["body"],
        ),
        Paragraph("2. Desarrollo", style["h1"]),
    ]
    for title, statement, solution in EXERCISES:
        story.append(Paragraph(title, style["h2"]))
        story.append(Paragraph(f"<b>Enunciado.</b> {statement}", style["statement"]))
        story.append(Paragraph(f"<b>Solución.</b> {solution}", style["body"]))

    story.extend([
        PageBreak(),
        Paragraph("3. Resultados reproducibles", style["h1"]),
        Paragraph("Corrida con semilla 22193 y parámetros predeterminados.", style["body"]),
    ])
    result_rows = [
        ["Ej.", "Configuración", "Resultado", "Referencia"],
        ["1", "1,000 variables", f"Media {result['ejercicio_1']['media_estimada']:.8f}", f"{result['ejercicio_1']['media_exacta']:.8f}"],
        ["4", "50,000 meses", f"P={result['ejercicio_4']['probabilidad_estimada']:.4%}", f"{result['ejercicio_4']['probabilidad_referencia']:.4%}"],
        ["5", "10,000 normales", f"m={result['ejercicio_5']['media']:.5f}; s2={result['ejercicio_5']['varianza']:.5f}", "m=0; var=1"],
        ["6", "lambda=2, T=10", f"{result['ejercicio_6']['eventos_observados']} eventos", "20 esperados"],
        ["7", "T=10", f"{result['ejercicio_7']['global_eventos']} global; {result['ejercicio_7']['mejorado_eventos']} mejorado", f"{result['ejercicio_7']['eventos_esperados']:.4f} esperados"],
        ["8", "lambda=1, R=5", f"{result['ejercicio_8']['puntos_observados']} puntos", f"{result['ejercicio_8']['puntos_esperados']:.4f}"],
        ["9", "10,000 normales", f"m={result['ejercicio_9']['media']:.5f}; s2={result['ejercicio_9']['varianza']:.5f}", "m=0; var=1"],
        ["10", "lambda=1, R=2", f"{result['ejercicio_10']['puntos_observados']} puntos", f"{result['ejercicio_10']['puntos_esperados']:.4f}"],
    ]
    table = Table(result_rows, colWidths=[0.38 * inch, 1.35 * inch, 2.25 * inch, 1.55 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B9CFC0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT_GREEN]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.extend([
        Paragraph("4. Auditoría contra instrucciones", style["h1"]),
        Paragraph(
            "La comprobación se efectuó contra los diez ejercicios y todos sus incisos del PDF de "
            "CC2017. No se encontró una rúbrica separada aplicable; la rúbrica localizada en Descargas "
            "corresponde a Construcción de Compiladores y no fue utilizada.",
            style["body"],
        ),
        Paragraph(
            "La auditoría incorporó los enunciados, optimizó el reciclaje exponencial del Ejercicio 5 "
            "y cubrió el extremo U=0 de la inversión Poisson espacial. Las 26 pruebas automatizadas "
            "y los diez formularios de Streamlit se ejecutaron sin excepciones.",
            style["body"],
        ),
        Paragraph("5. Conclusión", style["h1"]),
        Paragraph(
            "La práctica responde teórica y programáticamente a todos los requisitos disponibles. "
            "La separación por carpetas, la semilla documentada y las pruebas permiten reproducir y "
            "mantener el trabajo.",
            style["body"],
        ),
    ])
    document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Informe PDF generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()

