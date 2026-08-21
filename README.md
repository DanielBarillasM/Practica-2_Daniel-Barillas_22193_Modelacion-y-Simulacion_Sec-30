<div align="center">

# Práctica 2 — Generación de Variables Aleatorias Continuas

### CC2017 · Modelación y Simulación · Sección 30

**Universidad del Valle de Guatemala**  
**Pablo Daniel Barillas Moreno · Carné 22193**

[Repositorio de GitHub](https://github.com/DanielBarillasM/Practica-2_Daniel-Barillas_22193_Modelacion-y-Simulacion_Sec-30)

</div>

---

Aplicación educativa desarrollada con Streamlit para presentar la teoría, los
algoritmos y las simulaciones de los diez ejercicios de la Práctica 2. Cada
procedimiento conserva sus números aleatorios, muestra gráficas de diagnóstico
y permite descargar las tablas completas en CSV.

## Entregables principales

- [Aplicación Streamlit](app/app.py)
- [Informe académico en Word](docs/informe/Informe_Practica_2_Daniel_Barillas_22193.docx)
- [PDF de instrucciones](docs/instrucciones/Practica_2_Generacion_de_Variables_Aleatorias_Continuas.pdf)
- [Matriz de cumplimiento](docs/matriz_cumplimiento.md)
- [Pruebas automatizadas](tests/)

## Datos académicos

| Campo | Información |
|---|---|
| Universidad | Universidad del Valle de Guatemala |
| Facultad | Facultad de Ingeniería |
| Departamento | Ciencia de la Computación y Tecnologías de la Información |
| Curso | CC2017 — Modelación y Simulación |
| Período | Ciclo 2, 2026 |
| Sección | 30 |
| Estudiante | Pablo Daniel Barillas Moreno |
| Carné | 22193 |

## Características

- Diez secciones que corresponden uno a uno con el PDF.
- Respuestas teóricas visibles antes de ejecutar las simulaciones.
- Fórmulas renderizadas con LaTeX dentro de Streamlit.
- Generador PCG64 con semilla editable y valor inicial `22193`.
- Tablas auditables con uniformes, transformaciones y decisiones.
- Gráficas interactivas de distribución, convergencia y procesos espaciales.
- Comparaciones entre resultados simulados y referencias matemáticas.
- Descarga de resultados en CSV codificado en UTF-8.
- Código numérico separado de la interfaz y cubierto por pruebas automáticas.
- Informe académico en formato Word dentro de `docs/informe/`.

## Resultados reproducibles

La siguiente tabla corresponde a los parámetros predeterminados y a la semilla
`22193`. Una corrida con otra semilla producirá una trayectoria diferente, pero
debe mantener el mismo comportamiento probabilístico.

| Ejercicio | Configuración | Resultado reproducible | Referencia |
|---:|---|---:|---:|
| 1 | 1,000 observaciones | Media `0.02490814` | `0.02479168` |
| 4 | 50,000 meses | Probabilidad `10.6820 %` | `10.7098 %` |
| 5 | 10,000 normales | Media `0.005952`; varianza `0.992142` | Media 0; varianza 1 |
| 6 | λ=2, T=10 | 27 eventos | 20 esperados |
| 7 | T=10 | 25 eventos global; 38 mejorado | `39.5916` esperados |
| 8 | λ=1, R=5 | 73 puntos | `78.5398` esperados |
| 9 | 10,000 normales | Media `0.013458`; varianza `1.016333` | Media 0; varianza 1 |
| 10 | λ=1, R=2 | 10 puntos | `12.5664` esperados |

Los datos numéricos también se encuentran en
[`data/resultados_referencia.json`](data/resultados_referencia.json).

## Contenido matemático

### 1. Exponencial condicionada

Para una exponencial de tasa 1 condicionada a `X < a`, la transformación
inversa es:

```math
X=-\ln\left(1-U(1-e^{-a})\right).
```

Con `a=0.05`, el valor exacto solicitado es:

```math
E[X\mid X<a]=1-\frac{a}{e^a-1}=0.0247916753467\ldots
```

Este método es eficiente porque todas las variables generadas pertenecen al
intervalo solicitado; no se desperdician propuestas mediante rechazo.

### 2. Método de composición

Se genera un índice discreto `I` con `P(I=i)=p_i` y después se genera una
observación utilizando `F_i`. La ley de la probabilidad total demuestra que:

```math
P(X\le x)=\sum_{i=1}^{n}P(I=i)P(X\le x\mid I=i)
=\sum_{i=1}^{n}p_iF_i(x).
```

La aplicación incluye una mezcla editable para comprobar empíricamente esta
igualdad.

### 3. Distribuciones por composición

- Inciso (a): seleccionar equiprobablemente `J` entre 1, 3 y 5, y generar
  `X=U^(1/J)`.
- Inciso (b): seleccionar una exponencial de tasa 2 con probabilidad `1/3` o
  una uniforme en `(0,1)` con probabilidad `2/3`.
- Inciso (c): seleccionar `I=i` con probabilidad `α_i` y generar `X=U^(1/i)`.

### 4. Cartera de seguros

El número de reclamaciones y el monto mensual son:

```math
N\sim\mathrm{Binomial}(1000,0.05),\qquad
S=\sum_{i=1}^{N}Y_i,\qquad Y_i\sim\mathrm{Exp}(1/800).
```

Condicionado a `N=n`, el monto `S` es Gamma con forma `n` y escala 800. La
probabilidad de referencia utilizada para verificar la simulación es:

```math
P(S>50000)=0.10709770132248\ldots
```

### 5. Normal por rechazo exponencial

Se generan `Y1,Y2` exponenciales de tasa 1 y se acepta cuando:

```math
Y_2>\frac{(Y_1-1)^2}{2}.
```

Después se asigna signo con probabilidad `1/2`. La tasa de aceptación teórica
es `sqrt(π/(2e))`, aproximadamente `0.76017`.

### 6. Proceso de Poisson homogéneo

Se generan tiempos entre llegadas exponenciales y se acumulan hasta superar
`T`:

```math
E_i\sim\mathrm{Exp}(\lambda),\qquad
S_n=\sum_{i=1}^{n}E_i,qquad
N(T)\sim\mathrm{Poisson}(\lambda T).
```

### 7. Proceso de Poisson no homogéneo

La intensidad es:

```math
\lambda(t)=3+\frac{4}{t+1}.
```

El algoritmo inicial utiliza la cota global `M=7`. La mejora propuesta divide
el horizonte en intervalos unitarios y usa `M_k=λ(k)` porque la intensidad es
decreciente. Con la semilla de referencia, las propuestas bajan de 72 a 41.

```math
E[N(10)]=\int_0^{10}\lambda(t)\,dt
=30+4\ln(11)=39.59158109\ldots
```

### 8. Poisson bidimensional

Para un círculo de radio `R`:

```math
N\sim\mathrm{Poisson}(\lambda\pi R^2),\qquad
r=R\sqrt{U_1},\qquad \theta=2\pi U_2.
```

La raíz cuadrada es necesaria para producir puntos uniformes respecto del área
del círculo.

### 9. Método polar

El método de Marsaglia transforma dos uniformes al cuadrado `(-1,1)^2`, rechaza
los pares fuera del círculo unitario y calcula:

```math
S=V_1^2+V_2^2,qquad
X=V_1\sqrt{\frac{-2\ln S}{S}},\qquad
Y=V_2\sqrt{\frac{-2\ln S}{S}}.
```

Genera dos normales independientes sin evaluar funciones trigonométricas. Su
probabilidad de aceptación es `π/4`.

### 10. Proceso bidimensional: definición y ejemplo

Para cualquier región medible `A`:

```math
N(A)\sim\mathrm{Poisson}(\lambda |A|),
```

y los conteos de regiones disjuntas son independientes. La aplicación presenta
la definición, usos, algoritmo y un ejemplo completo para `λ=1` y `R=2`.

## Instalación

Se recomienda Python 3.11 o superior.

```powershell
git clone https://github.com/DanielBarillasM/Practica-2_Daniel-Barillas_22193_Modelacion-y-Simulacion_Sec-30.git
cd Practica-2_Daniel-Barillas_22193_Modelacion-y-Simulacion_Sec-30
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecutar la aplicación

Desde la raíz del repositorio:

```powershell
streamlit run app\app.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`.

## Ejecutar las pruebas

Suite completa:

```powershell
python -m pytest -q
```

Solo las pruebas matemáticas:

```powershell
python -m pytest tests\test_simulations.py -v
```

Solo las pruebas de interfaz:

```powershell
python -m pytest tests\test_app.py -v
```

Los archivos de prueba son módulos de `pytest`; no deben ejecutarse directamente
con `python tests\test_simulations.py`.

## Regenerar el informe Word

Primero se pueden recalcular los resultados predeterminados:

```powershell
python scripts\generar_resultados.py
```

Después se construye el documento:

```powershell
python scripts\generar_informe.py
```

El documento se crea en:

```text
docs/informe/Informe_Practica_2_Daniel_Barillas_22193.docx
```

## Organización del repositorio

```text
.
├── app/
│   └── app.py                         # Interfaz Streamlit
├── assets/
│   └── styles.css                     # Identidad visual
├── data/
│   └── resultados_referencia.json     # Corrida reproducible
├── docs/
│   ├── informe/                       # Informe académico Word
│   ├── instrucciones/                 # PDF proporcionado
│   └── matriz_cumplimiento.md          # Auditoría contra el PDF
├── scripts/
│   ├── generar_informe.py             # Generador del DOCX
│   └── generar_resultados.py           # Corrida reproducible
├── src/
│   └── practica2/
│       ├── models.py                  # Contenedores de resultados
│       └── simulations.py             # Algoritmos matemáticos
├── tests/
│   ├── test_app.py                    # Pruebas de las diez páginas
│   └── test_simulations.py            # Pruebas teóricas y estadísticas
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── pytest.ini
└── README.md
```

## Reproducibilidad

Elegí `22193`, mi número de carné, como semilla inicial para que la corrida de
referencia pueda repetirse. La semilla únicamente inicializa PCG64; no significa
que se utilice el mismo número en todos los lanzamientos. Cambiarla produce una
nueva trayectoria válida y mantenerla reproduce exactamente las mismas tablas.

## Consideraciones

- Una sola trayectoria de Poisson puede alejarse de su esperanza sin ser un
  error de programación.
- Los intervalos de confianza mostrados son aproximaciones normales del 95 %.
- Las referencias exactas se utilizan para validar, no para reemplazar, la
  simulación solicitada.
- Los parámetros fijados explícitamente por el PDF aparecen identificados en la
  interfaz.

---

<div align="center">

Desarrollado para **CC2017 — Modelación y Simulación**  
Universidad del Valle de Guatemala · Ciclo 2, 2026

</div>
