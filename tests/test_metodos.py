"""Pruebas del motor numérico (``metodos.py``).

Ejecutar con::

    ./venv/bin/python -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import metodos as M


class TestErrorRelativo(unittest.TestCase):
    def test_caso_normal(self):
        self.assertAlmostEqual(M.error_relativo(10, 9), 10.0)

    def test_actual_cero(self):
        self.assertEqual(M.error_relativo(0, 0), 0.0)
        self.assertEqual(M.error_relativo(0, 1), float("inf"))

    def test_valores_negativos(self):
        self.assertAlmostEqual(M.error_relativo(-0.5, -1), 100.0)


class TestPreparacionFuncion(unittest.TestCase):
    def test_texto_y_derivada(self):
        f, df = M.preparar_funcion("x**2 - 4")
        self.assertAlmostEqual(f(3), 5.0)
        self.assertAlmostEqual(df(3), 6.0)

    def test_variable_invalida(self):
        with self.assertRaises(ValueError):
            M.preparar_funcion("y**2 - 1")

    def test_expresion_invalida(self):
        with self.assertRaises(ValueError):
            M.preparar_funcion("x**")


class TestBiseccion(unittest.TestCase):
    def test_raiz_conocida(self):
        resultado = M.biseccion(-1, 0)
        self.assertTrue(resultado.convergio)
        self.assertAlmostEqual(resultado.raiz, -0.764014925, places=5)
        self.assertLess(abs(M.funcion(resultado.raiz)), 1e-6)
        self.assertGreater(len(resultado.iteraciones), 0)

    def test_sin_cambio_de_signo(self):
        resultado = M.biseccion(2, 3)
        self.assertFalse(resultado.convergio)
        self.assertIsNone(resultado.raiz)
        self.assertIn("cambio de signo", resultado.mensaje)

    def test_intervalo_invalido(self):
        resultado = M.biseccion(1, 0)
        self.assertFalse(resultado.convergio)
        self.assertIn("menor", resultado.mensaje)

    def test_extremos_son_raices(self):
        resultado = M.biseccion(1, 2, f="x**2 - 1")
        self.assertTrue(resultado.convergio)
        self.assertAlmostEqual(resultado.raiz, 1.0)


class TestMuller(unittest.TestCase):
    def test_raiz_real(self):
        resultado = M.muller(0, 0.5, 1)
        self.assertTrue(resultado.convergio)
        self.assertAlmostEqual(resultado.raiz.real, 1.396338531, places=5)
        self.assertAlmostEqual(resultado.raiz.imag, 0.0, places=6)

    def test_puntos_repetidos(self):
        resultado = M.muller(1, 1, 2)
        self.assertFalse(resultado.convergio)
        self.assertIn("distintos", resultado.mensaje)


class TestNewton(unittest.TestCase):
    def test_raiz_doble(self):
        resultado = M.newton_raphson("x**3 - 4*x**2 + 5*x - 2", 0)
        self.assertTrue(resultado.convergio)
        self.assertAlmostEqual(resultado.raiz, 1.0, places=2)

    def test_callable(self):
        resultado = M.newton_raphson(lambda x: x * x - 4, 1)
        self.assertTrue(resultado.convergio)
        self.assertAlmostEqual(resultado.raiz, 2.0, places=5)

    def test_derivada_nula(self):
        resultado = M.newton_raphson("x**2 + 1", 0)
        self.assertFalse(resultado.convergio)
        self.assertIn("derivada", resultado.mensaje)


class TestBairstow(unittest.TestCase):
    def test_factor_cuadratico(self):
        resultado = M.bairstow([1, -4, 2, 3, -1], -2, -2)
        self.assertTrue(resultado.convergio)
        self.assertEqual(len(resultado.raices), 2)
        for raiz in resultado.raices:
            self.assertLess(abs(M.funcion(raiz)), 1e-6)

        m = resultado.extra["m"]
        n = resultado.extra["n"]
        # El factor x**2 - m*x - n debe dividir exactamente al polinomio.
        residuo_0, residuo_1 = resultado.extra["residuos"]
        self.assertLess(abs(residuo_0), 1e-9)
        self.assertLess(abs(residuo_1), 1e-9)
        self.assertAlmostEqual(M.funcion((m + (m * m + 4 * n) ** 0.5) / 2), 0, places=6)

    def test_grado_insuficiente(self):
        resultado = M.bairstow([1, 0, 1], 0.1, 0.1)
        self.assertFalse(resultado.convergio)
        self.assertIn("grado", resultado.mensaje)

    def test_polinomio_nulo(self):
        resultado = M.bairstow([0, 0, 0, 0], 0.1, 0.1)
        self.assertFalse(resultado.convergio)
        self.assertIn("nulo", resultado.mensaje)


class TestDivisionSintetica(unittest.TestCase):
    def test_residuo_casi_cero(self):
        resultado = M.division_sintetica([1, -4, 2, 3, -1], -0.764014925)
        self.assertAlmostEqual(resultado.extra["residuo"], 0.0, places=5)
        self.assertEqual(len(resultado.extra["coeficientes"]), 4)

    def test_cociente_correcto(self):
        resultado = M.division_sintetica([1, -4, 2, 3, -1], 1)
        # x^4-4x^3+2x^2+3x-1 entre (x-1): cociente 1 -3 -1 2 y residuo 1
        self.assertEqual(resultado.extra["coeficientes"], [1.0, -3.0, -1.0, 2.0])
        self.assertAlmostEqual(resultado.extra["residuo"], 1.0)

    def test_polinomio_muy_corto(self):
        with self.assertRaises(ValueError):
            M.division_sintetica([1], 2)


class TestImportacion(unittest.TestCase):
    def test_importar_no_ejecuta_nada(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        salida = subprocess.run(
            [sys.executable, "-c", "import metodos"],
            cwd=raiz,
            capture_output=True,
            text=True,
        )
        self.assertEqual(salida.returncode, 0, salida.stderr)
        self.assertEqual(salida.stdout, "")


if __name__ == "__main__":
    unittest.main()
