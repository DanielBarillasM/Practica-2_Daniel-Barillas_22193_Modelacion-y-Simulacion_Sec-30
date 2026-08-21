"""Prueba de humo de todas las páginas Streamlit sin iniciar un navegador."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app" / "app.py"

PAGES = [
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


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_without_exception(page: str) -> None:
    """Comprueba que cada página abre y presenta el enunciado correspondiente.

    ``AppTest`` ejecuta Streamlit sin navegador. La parametrización recorre el
    mismo catálogo que ve el usuario, selecciona cada opción y vuelve a ejecutar
    la aplicación. Así se detectan fallos de importación, componentes incompatibles
    o páginas que hayan perdido el encabezado requerido por las instrucciones.
    """

    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.selectbox[0].select(page).run()
    assert not app.exception
    assert any("Enunciado del ejercicio" == item.value for item in app.subheader)
