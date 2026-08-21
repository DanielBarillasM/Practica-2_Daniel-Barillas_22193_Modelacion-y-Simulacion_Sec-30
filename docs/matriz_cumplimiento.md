# Matriz de cumplimiento de la Práctica 2

Esta matriz relaciona cada requisito del PDF con su respuesta teórica, su
implementación y la evidencia visible en Streamlit.

## Documento usado como criterio

La evaluación se hizo contra el PDF de la **Práctica 2 de CC2017**. No se
proporcionó una rúbrica separada correspondiente a esta actividad. La rúbrica
localizada en Descargas pertenece al curso Construcción de Compiladores y no es
aplicable a generación de variables aleatorias continuas.

Cada pantalla muestra ahora el enunciado correspondiente antes de la solución,
lo cual permite comprobar directamente que teoría e implementación respondan al
problema correcto.

| Ejercicio | Requisito del PDF | Respuesta implementada | Evidencia |
|---:|---|---|---|
| 1 | Algoritmo eficiente, 1,000 variables, estimación y valor exacto | Transformación inversa de la exponencial truncada; media, IC y derivación exacta | Tabla de 1,000 valores, histograma y convergencia |
| 2 | Explicar el método de composición | Selección de índice con pesos `p_i` y demostración por probabilidad total | Explicación LaTeX y mezcla editable |
| 3(a) | Generar CDF `(x+x³+x⁵)/3` | Mezcla equiprobable de potencias 1, 3 y 5 | CDF teórica/empírica y tabla de componentes |
| 3(b) | Generar la CDF por tramos | Mezcla de exponencial de tasa 2 y uniforme `(0,1)` | CDF, histograma y muestras auditables |
| 3(c) | Generar `Σ α_i x^i` | Selección de `i` con probabilidad `α_i`; transformación `U^(1/i)` | Pesos editables, CDF y tabla |
| 4 | Estimar `P(S>50000)` | Cartera binomial compuesta con suma Gamma equivalente | Probabilidad, IC, referencia, histograma y convergencia |
| 5 | Normal por rechazo exponencial del Ejemplo 5f | Rechazo con dos exponenciales, signo equiprobable y reciclaje del residual independiente | Intentos, eficiencia, histograma, media y varianza |
| 6 | Primeras `T` unidades de un Poisson de tasa `λ` | Tiempos entre llegadas exponenciales acumulados hasta superar `T` | Trayectoria escalonada y tabla de llegadas |
| 7(a) | Adelgazamiento en `[0,10]` para la intensidad indicada | Cota global `M=7` y aceptación `λ(t)/M` | Tabla completa de propuestas y eventos |
| 7(b) | Proponer una mejora | Cotas decrecientes por intervalos unitarios | Comparación de propuestas y eficiencia |
| 8 | Poisson bidimensional con `λ=1`, `R=5` | Conteo Poisson y puntos uniformes con `r=R√U` | Gráfica circular y coordenadas completas |
| 9(a) | Explicar el método polar | Algoritmo de Marsaglia paso a paso | Teoría y pseudocódigo |
| 9(b) | Explicar para qué sirve | Generación de pares normales sin trigonometría | Comparación conceptual y aceptación `π/4` |
| 9(c) | Ejemplo numérico | Ejemplo con `U1=0.70`, `U2=0.40` | Cálculos intermedios y par normal resultante |
| 10(a) | Definición formal y algoritmo espacial | Propiedad Poisson por área e independencia en regiones disjuntas | Teoría y pseudocódigo |
| 10(b) | Aplicaciones | Accidentes, defectos, árboles, impactos, antenas y otros fenómenos | Pestaña de aplicaciones |
| 10(c) | Ejemplo con `λ=1`, `R=2` | Conteo por inversión y coordenadas polares de cada punto | Tabla y gráfica reproducibles |

## Validación técnica

- El código matemático no depende de Streamlit.
- Los parámetros fijados por el PDF se conservan en las ejecuciones requeridas.
- La semilla `22193` permite repetir la corrida documentada.
- Las 26 pruebas comprueban soporte, momentos, CDF, tasas de aceptación, conteos y
  restricciones espaciales.
- Las diez páginas de Streamlit se renderizan sin excepciones.
- Cada página contiene el enunciado del ejercicio antes de su solución.
- El extremo `U=0` de la inversión Poisson devuelve correctamente un conteo 0.
- El Ejercicio 5 reproduce las 1.64 exponenciales y 1.32 evaluaciones cuadráticas
  por normal indicadas aproximadamente en el material.
