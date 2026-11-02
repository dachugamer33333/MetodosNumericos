"""Motor numérico para la búsqueda de raíces de ecuaciones.

Convención de coeficientes
--------------------------
Los polinomios se reciben con los coeficientes ordenados de **mayor a menor
grado** (el coeficiente principal primero). Por ejemplo::

    [1, -4, 2, 3, -1]  ->  x**4 - 4*x**3 + 2*x**2 + 3*x - 1

Cada método devuelve un :class:`Resultado` con la raíz, la tabla de
iteraciones y un mensaje descriptivo, de forma que pueda usarse tanto desde
la consola como desde la interfaz gráfica.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field

import sympy as sp


@dataclass
class Resultado:
    """Resultado homogéneo de cualquier método numérico."""

    metodo: str
    columnas: list[str] = field(default_factory=list)
    iteraciones: list[list] = field(default_factory=list)
    raiz: complex | float | None = None
    raices: list[complex] = field(default_factory=list)
    convergio: bool = False
    mensaje: str = ""
    extra: dict = field(default_factory=dict)


def funcion(x):
    """Función de ejemplo usada por los métodos cuando no se indica otra."""
    return x**4 - 4 * x**3 + 2 * x**2 + 3 * x - 1


def error_relativo(actual, anterior):
    """Error relativo porcentual entre dos aproximaciones.

    Si ``actual`` es cero devuelve ``inf`` (salvo que ambas lo sean), para no
    ocultar un posible problema de convergencia.
    """
    if actual == 0:
        return 0.0 if anterior == 0 else math.inf
    return abs((actual - anterior) / actual) * 100


def preparar_funcion(expresion):
    """Convierte texto o callable en funciones numéricas ``(f, f')``.

    Parameters
    ----------
    expresion:
        Cadena evaluable por SymPy (por ejemplo ``"x**3 - 2*x + 1"``) o un
        callable de una sola variable. Para un callable la derivada es
        ``None`` (se calcula numéricamente si hace falta).
    """
    if callable(expresion):
        return expresion, None

    x = sp.Symbol("x")
    try:
        expr = sp.sympify(expresion)
    except (sp.SympifyError, SyntaxError) as exc:
        raise ValueError(f"La función no es válida: {expresion!r}") from exc

    variables = expr.free_symbols - {x}
    if variables:
        nombres = ", ".join(sorted(str(v) for v in variables))
        raise ValueError(f"La función solo puede usar la variable x (encontradas: {nombres}).")

    try:
        f = sp.lambdify(x, expr, modules=["math"])
        df = sp.lambdify(x, sp.diff(expr, x), modules=["math"])
    except Exception as exc:  # pragma: no cover - depende de SymPy
        raise ValueError(f"No se pudo preparar la función: {exc}") from exc

    return f, df


def _como_funcion(expresion):
    """Normaliza texto/callable a una función numérica."""
    return preparar_funcion(expresion)[0]


def _derivada_numerica(f, x, h=1e-7):
    return (f(x + h) - f(x - h)) / (2 * h)


def biseccion(a, b, tol=1e-6, max_iter=100, f=funcion):
    """Método de bisección en el intervalo ``[a, b]``.

    ``tol`` es la tolerancia del error relativo porcentual.
    """
    columnas = ["Iteración", "a", "b", "pn", "f(pn)", "Error %"]
    f = _como_funcion(f)
    tabla = []

    if a >= b:
        return Resultado(
            "Bisección",
            columnas,
            tabla,
            mensaje="El límite inferior debe ser menor que el superior.",
        )

    fa, fb = f(a), f(b)
    if fa == 0:
        return Resultado("Bisección", columnas, [], raiz=a, convergio=True,
                         mensaje=f"f({a:g}) = 0, la raíz es {a:g}.")
    if fb == 0:
        return Resultado("Bisección", columnas, [], raiz=b, convergio=True,
                         mensaje=f"f({b:g}) = 0, la raíz es {b:g}.")
    if fa * fb > 0:
        return Resultado(
            "Bisección",
            columnas,
            tabla,
            mensaje="El intervalo no tiene cambio de signo, no aplica bisección.",
        )

    pn_anterior = a
    pn = a
    convergio = False
    for i in range(1, max_iter + 1):
        pn = (a + b) / 2
        fpn = f(pn)
        err = error_relativo(pn, pn_anterior)
        tabla.append([i, a, b, pn, fpn, err])

        if fpn == 0 or err < tol:
            convergio = True
            break

        if fa * fpn < 0:
            b = pn
        else:
            a = pn
            fa = fpn
        pn_anterior = pn

    if convergio:
        mensaje = f"Raíz aproximada: {pn:.10g} (error {err:.3e} %)."
    else:
        mensaje = f"Se alcanzó el máximo de iteraciones ({max_iter})."

    return Resultado("Bisección", columnas, tabla, raiz=pn, convergio=convergio,
                     mensaje=mensaje)


def muller(a, b, c, max_iter=100, tol=1e-6, f=funcion):
    """Método de Müller a partir de tres aproximaciones ``a``, ``b`` y ``c``.

    ``tol`` es la tolerancia del error relativo porcentual.
    """
    columnas = ["Iteración", "a", "b", "c", "d", "Error %"]
    f = _como_funcion(f)
    tabla = []
    d = c

    for i in range(1, max_iter + 1):
        h0 = b - a
        h1 = c - b
        if h0 == 0 or h1 == 0 or (h0 + h1) == 0:
            return Resultado(
                "Müller", columnas, tabla, raiz=d,
                mensaje="Los puntos iniciales deben ser distintos entre sí.",
            )

        delta0 = (f(b) - f(a)) / h0
        delta1 = (f(c) - f(b)) / h1
        A = (delta1 - delta0) / (h1 + h0)
        B = A * h1 + delta1
        C = f(c)

        discriminante = cmath.sqrt(B**2 - 4 * A * C)

        # El denominador de mayor magnitud da la raíz más estable.
        if abs(B + discriminante) > abs(B - discriminante):
            denominador = B + discriminante
        else:
            denominador = B - discriminante

        if denominador == 0:
            return Resultado(
                "Müller", columnas, tabla, raiz=d,
                mensaje="El denominador se anuló; el método no puede continuar.",
            )

        d = c - (2 * C) / denominador
        err = error_relativo(d, c)
        tabla.append([i, a, b, c, d, err])

        if err < tol:
            return Resultado(
                "Müller", columnas, tabla, raiz=d, convergio=True,
                mensaje=f"Raíz aproximada: {d:.10g} (error {err:.3e} %).",
            )

        a, b, c = b, c, d

    return Resultado(
        "Müller", columnas, tabla, raiz=d,
        mensaje=f"Se alcanzó el máximo de iteraciones ({max_iter}).",
    )


def _coeficientes_b(a, m, n):
    """Coeficientes de la división de ``a`` entre ``x**2 - m*x - n``.

    ``a`` está en orden ascendente (``a[0]`` es el término constante). El
    resultado ``b`` también es ascendente: ``b[0]`` es el residuo,
    ``b[1:]`` los coeficientes del cociente.
    """
    grado = len(a) - 1
    b = [0.0] * (grado + 1)
    b[grado] = a[grado]
    b[grado - 1] = a[grado - 1] + m * b[grado]
    for i in range(grado - 2, -1, -1):
        b[i] = a[i] + m * b[i + 1] + n * b[i + 2]
    return b


def bairstow(condicion_inicial, m, n, tol=1e-6, max_iter=100):
    """Método de Bairstow para hallar el factor cuadrático ``x**2 - m*x - n``.

    ``condicion_inicial`` son los coeficientes del polinomio de mayor a menor
    grado. Se requieren al menos grado 3 para formar el sistema 2x2.
    ``tol`` es la tolerancia del error relativo porcentual de ``m`` y ``n``.
    """
    columnas = ["Iteración", "m", "n", "Error % m", "Error % n"]
    tabla = []

    try:
        descendente = [float(coef) for coef in condicion_inicial]
    except (TypeError, ValueError) as exc:
        raise ValueError("Los coeficientes deben ser numéricos.") from exc

    if len(descendente) < 4:
        return Resultado(
            "Bairstow", columnas, tabla,
            mensaje="Se requiere un polinomio de grado 3 o mayor.",
        )
    if all(abs(coef) < 1e-15 for coef in descendente):
        return Resultado(
            "Bairstow", columnas, tabla,
            mensaje="El polinomio no puede ser el polinomio nulo.",
        )

    # El algoritmo trabaja con coeficientes ascendentes.
    a = list(reversed(descendente))
    grado = len(a) - 1

    m_prev, n_prev = m, n
    convergio = False
    b = _coeficientes_b(a, m, n)

    for i in range(1, max_iter + 1):
        # Coeficientes b y c para el (m, n) actual.
        b = _coeficientes_b(a, m, n)
        c = [0.0] * (grado + 1)
        c[grado] = b[grado]
        c[grado - 1] = b[grado - 1] + m * c[grado]
        for j in range(grado - 2, -1, -1):
            c[j] = b[j] + m * c[j + 1] + n * c[j + 2]

        det = c[2] ** 2 - c[1] * c[3]
        if abs(det) < 1e-14:
            return Resultado(
                "Bairstow", columnas, tabla,
                mensaje="El determinante se anuló; prueba otros valores de m y n.",
            )

        delta_m = (b[0] * c[3] - b[1] * c[2]) / det
        delta_n = (b[1] * c[1] - b[0] * c[2]) / det

        m += delta_m
        n += delta_n

        err_m = error_relativo(m, m_prev)
        err_n = error_relativo(n, n_prev)
        tabla.append([i, m, n, err_m, err_n])

        # Residuo del factor con los nuevos valores.
        b = _coeficientes_b(a, m, n)
        residuo = max(abs(b[0]), abs(b[1]))

        m_prev, n_prev = m, n
        if (err_m < tol and err_n < tol) or residuo < 1e-12:
            convergio = True
            break

    # Raíces del factor cuadrático x**2 - m*x - n.
    discriminante = cmath.sqrt(m * m + 4 * n)
    raices = [(m + discriminante) / 2, (m - discriminante) / 2]

    # Cociente deflactado: b[1:] es ascendente, se devuelve descendente.
    deflactado = list(reversed(b[1:]))

    if convergio:
        def termino(valor):
            return ("+ " if valor >= 0 else "- ") + f"{abs(valor):.10g}"

        mensaje = (
            f"Factor: x² {termino(-m)}x {termino(-n)}. "
            f"Raíces: {raices[0]:.10g}, {raices[1]:.10g}."
        )
    else:
        mensaje = f"Se alcanzó el máximo de iteraciones ({max_iter})."

    return Resultado(
        "Bairstow", columnas, tabla, raices=raices, convergio=convergio,
        mensaje=mensaje,
        extra={
            "m": m,
            "n": n,
            "residuos": (b[0], b[1]),
            "polinomio_deflactado": deflactado,
        },
    )


def newton_raphson(funcion_str, x0, tol=1e-6, max_iter=100, df=None):
    """Método de Newton-Raphson.

    ``funcion_str`` puede ser una cadena (se deriva simbólicamente con SymPy)
    o un callable (en cuyo caso se usa ``df`` o una derivada numérica).
    ``tol`` es la tolerancia del error relativo porcentual y también se usa
    como criterio absoluto sobre ``|f(x)|``.
    """
    columnas = ["Iteración", "x_i", "f(x_i)", "f'(x_i)", "x_(i+1)", "Error %"]
    tabla = []

    f, df_calculada = preparar_funcion(funcion_str)
    if df is not None:
        df_calculada = _como_funcion(df)
    if df_calculada is None:
        df_calculada = lambda x: _derivada_numerica(f, x)

    x = x0
    err = math.inf
    convergio = False
    for i in range(1, max_iter + 1):
        y = f(x)
        dy = df_calculada(x)

        if abs(dy) < 1e-14:
            return Resultado(
                "Newton-Raphson", columnas, tabla, raiz=x,
                mensaje="La derivada es cercana a cero; el método no puede continuar.",
            )

        x_nuevo = x - y / dy
        err = error_relativo(x_nuevo, x)
        tabla.append([i, x, y, dy, x_nuevo, err])

        # El error relativo puede no bajar en raíces múltiples; se acepta
        # también el criterio absoluto sobre |f(x)|.
        convergio = err < tol or abs(f(x_nuevo)) < tol
        x = x_nuevo
        if convergio:
            break

    if convergio:
        mensaje = f"Raíz aproximada: {x:.10g} (error {err:.3e} %)."
    else:
        mensaje = f"Se alcanzó el máximo de iteraciones ({max_iter})."

    return Resultado("Newton-Raphson", columnas, tabla, raiz=x,
                     convergio=convergio, mensaje=mensaje)


def division_sintetica(polinomio, r):
    """División sintética de ``polinomio`` entre ``(x - r)``.

    ``polinomio`` está de mayor a menor grado. Devuelve el cociente y el
    residuo en ``extra``.
    """
    columnas = ["Paso", "Coeficiente original", "Coeficiente b", "r · b anterior"]
    try:
        coeficientes = [float(coef) for coef in polinomio]
    except (TypeError, ValueError) as exc:
        raise ValueError("Los coeficientes deben ser numéricos.") from exc

    if len(coeficientes) < 2:
        raise ValueError("Se requieren al menos dos coeficientes.")

    n = len(coeficientes)
    cociente = [0.0] * n
    cociente[0] = coeficientes[0]

    tabla = [[f"b_{n - 1}", coeficientes[0], cociente[0], None]]
    for i in range(1, n):
        cociente[i] = coeficientes[i] + r * cociente[i - 1]
        etiqueta = f"b_{n - 1 - i}" if i < n - 1 else "Residuo"
        tabla.append([etiqueta, coeficientes[i], cociente[i], r * cociente[i - 1]])

    nuevos = cociente[:-1]
    residuo = cociente[-1]

    return Resultado(
        "División sintética", columnas, tabla,
        mensaje=f"Cociente de grado {n - 2}, residuo = {residuo:.3e}.",
        convergio=True,
        extra={"coeficientes": nuevos, "residuo": residuo},
    )


if __name__ == "__main__":
    for resultado in (
        biseccion(-1, 0),
        muller(0, 0.5, 1),
        newton_raphson("x**3 - 4*x**2 + 5*x - 2", 0),
        bairstow([1, -4, 2, 3, -1], -2, -2),
    ):
        print(f"{resultado.metodo}: {resultado.mensaje}")
