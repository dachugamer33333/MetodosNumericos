"""Interfaz gráfica de los métodos numéricos de búsqueda de raíces."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

import metodos as M


FUNCION_DEFECTO = "x**4 - 4*x**3 + 2*x**2 + 3*x - 1"
COEFICIENTES_DEFECTO = "1 -4 2 3 -1"


def formatear(valor, decimales=8):
    """Devuelve una cadena legible para cualquier valor de la tabla."""
    if valor is None:
        return "—"
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, str):
        return valor
    if isinstance(valor, complex):
        if abs(valor.imag) < 1e-10:
            return formatear(valor.real, decimales)
        return f"{valor.real:.6g} {valor.imag:+.6g}i"

    numero = float(valor)
    if math.isinf(numero):
        return "∞" if numero > 0 else "-∞"
    if math.isnan(numero):
        return "NaN"
    if numero != 0 and (abs(numero) < 1e-4 or abs(numero) >= 1e6):
        return f"{numero:.6e}"
    return f"{numero:.{decimales}f}"


def leer_float(variable, nombre):
    texto = variable.get().strip().replace(",", ".")
    if not texto:
        raise ValueError(f"Falta el valor de {nombre}.")
    try:
        return float(texto)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un número.") from exc


def leer_entero(variable, nombre):
    valor = leer_float(variable, nombre)
    if valor != int(valor) or valor < 1:
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    return int(valor)


def leer_coeficientes(variable, minimo=2):
    partes = variable.get().strip().replace(",", " ").split()
    if len(partes) < minimo:
        raise ValueError(f"Introduce al menos {minimo} coeficientes.")
    try:
        return [float(parte) for parte in partes]
    except ValueError as exc:
        raise ValueError("Los coeficientes deben ser números separados por espacios.") from exc


class Tabla(ttk.Frame):
    """Tabla reutilizable para mostrar las iteraciones de un método."""

    def __init__(self, master):
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, show="headings")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

    def mostrar(self, resultado):
        columnas = resultado.columnas
        self.tree["columns"] = columnas
        for columna in columnas:
            self.tree.heading(columna, text=columna)
            self.tree.column(columna, width=130, minwidth=80, anchor="center")

        self.tree.delete(*self.tree.get_children())
        for fila in resultado.iteraciones:
            self.tree.insert("", "end", values=[formatear(valor) for valor in fila])


class TabBase(ttk.Frame):
    """Base común: panel de parámetros, botón, estado y tabla."""

    titulo = "Método"

    def __init__(self, master):
        super().__init__(master, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.params = ttk.LabelFrame(self, text="Parámetros", padding=10)
        self.params.grid(row=0, column=0, sticky="ew")
        self.params.columnconfigure(7, weight=1)

        barra = ttk.Frame(self)
        barra.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        ttk.Button(barra, text="Calcular", command=self.calcular).pack(side="left")
        self.estado = ttk.Label(
            barra, text="Introduce los datos y pulsa Calcular.", wraplength=760
        )
        self.estado.pack(side="left", padx=12)

        self.tabla = Tabla(self)
        self.tabla.grid(row=2, column=0, sticky="nsew")

    def agregar_funcion(self, fila, etiqueta="f(x) ="):
        ttk.Label(self.params, text=etiqueta).grid(row=fila, column=0, sticky="w")
        ttk.Entry(self.params, textvariable=self.funcion, width=62).grid(
            row=fila, column=1, columnspan=7, sticky="we", padx=(6, 0)
        )

    def agregar_campo(self, fila, columna, etiqueta, variable):
        ttk.Label(self.params, text=etiqueta).grid(
            row=fila, column=columna * 2, sticky="w", padx=(0, 4), pady=3
        )
        ttk.Entry(self.params, textvariable=variable, width=14).grid(
            row=fila, column=columna * 2 + 1, sticky="w", padx=(0, 14), pady=3
        )

    def agregar_coeficientes(self, fila, etiqueta="Coeficientes (mayor → menor grado):"):
        ttk.Label(self.params, text=etiqueta).grid(row=fila, column=0, sticky="w")
        ttk.Entry(self.params, textvariable=self.coeficientes, width=52).grid(
            row=fila, column=1, columnspan=7, sticky="we", padx=(6, 0)
        )

    def calcular(self):
        try:
            resultado = self.ejecutar()
        except Exception as exc:
            self.estado.configure(text=str(exc), foreground="#b71c1c")
            messagebox.showerror("No se pudo calcular", str(exc))
            return

        self.tabla.mostrar(resultado)
        self.estado.configure(
            text=resultado.mensaje,
            foreground="#1b5e20" if resultado.convergio else "#b71c1c",
        )

    def ejecutar(self):  # pragma: no cover - implementado en cada pestaña
        raise NotImplementedError


class TabBiseccion(TabBase):
    titulo = "Bisección"

    def __init__(self, master):
        super().__init__(master)
        self.funcion = tk.StringVar(value=FUNCION_DEFECTO)
        self.a = tk.StringVar(value="-1")
        self.b = tk.StringVar(value="0")
        self.tol = tk.StringVar(value="1e-6")
        self.max_iter = tk.StringVar(value="100")

        self.agregar_funcion(0)
        self.agregar_campo(1, 0, "a =", self.a)
        self.agregar_campo(1, 1, "b =", self.b)
        self.agregar_campo(1, 2, "Tolerancia (%) =", self.tol)
        self.agregar_campo(1, 3, "Máx. iteraciones =", self.max_iter)

    def ejecutar(self):
        return M.biseccion(
            leer_float(self.a, "a"),
            leer_float(self.b, "b"),
            tol=leer_float(self.tol, "la tolerancia"),
            max_iter=leer_entero(self.max_iter, "el máximo de iteraciones"),
            f=self.funcion.get(),
        )


class TabMuller(TabBase):
    titulo = "Müller"

    def __init__(self, master):
        super().__init__(master)
        self.funcion = tk.StringVar(value=FUNCION_DEFECTO)
        self.a = tk.StringVar(value="0")
        self.b = tk.StringVar(value="0.5")
        self.c = tk.StringVar(value="1")
        self.tol = tk.StringVar(value="1e-6")
        self.max_iter = tk.StringVar(value="100")

        self.agregar_funcion(0)
        self.agregar_campo(1, 0, "a =", self.a)
        self.agregar_campo(1, 1, "b =", self.b)
        self.agregar_campo(1, 2, "c =", self.c)
        self.agregar_campo(1, 3, "Tolerancia (%) =", self.tol)
        self.agregar_campo(1, 4, "Máx. iteraciones =", self.max_iter)

    def ejecutar(self):
        return M.muller(
            leer_float(self.a, "a"),
            leer_float(self.b, "b"),
            leer_float(self.c, "c"),
            max_iter=leer_entero(self.max_iter, "el máximo de iteraciones"),
            tol=leer_float(self.tol, "la tolerancia"),
            f=self.funcion.get(),
        )


class TabNewton(TabBase):
    titulo = "Newton-Raphson"

    def __init__(self, master):
        super().__init__(master)
        self.funcion = tk.StringVar(value="x**3 - 4*x**2 + 5*x - 2")
        self.x0 = tk.StringVar(value="0")
        self.tol = tk.StringVar(value="1e-6")
        self.max_iter = tk.StringVar(value="100")

        self.agregar_funcion(0)
        self.agregar_campo(1, 0, "x0 =", self.x0)
        self.agregar_campo(1, 1, "Tolerancia (%) =", self.tol)
        self.agregar_campo(1, 2, "Máx. iteraciones =", self.max_iter)

    def ejecutar(self):
        return M.newton_raphson(
            self.funcion.get(),
            leer_float(self.x0, "x0"),
            tol=leer_float(self.tol, "la tolerancia"),
            max_iter=leer_entero(self.max_iter, "el máximo de iteraciones"),
        )


class TabBairstow(TabBase):
    titulo = "Bairstow"

    def __init__(self, master):
        super().__init__(master)
        self.coeficientes = tk.StringVar(value=COEFICIENTES_DEFECTO)
        self.m = tk.StringVar(value="-2")
        self.n = tk.StringVar(value="-2")
        self.tol = tk.StringVar(value="1e-6")
        self.max_iter = tk.StringVar(value="100")

        self.agregar_coeficientes(0)
        self.agregar_campo(1, 0, "m =", self.m)
        self.agregar_campo(1, 1, "n =", self.n)
        self.agregar_campo(1, 2, "Tolerancia (%) =", self.tol)
        self.agregar_campo(1, 3, "Máx. iteraciones =", self.max_iter)

    def ejecutar(self):
        return M.bairstow(
            leer_coeficientes(self.coeficientes, minimo=4),
            leer_float(self.m, "m"),
            leer_float(self.n, "n"),
            tol=leer_float(self.tol, "la tolerancia"),
            max_iter=leer_entero(self.max_iter, "el máximo de iteraciones"),
        )


class TabDivisionSintetica(TabBase):
    titulo = "División sintética"

    def __init__(self, master):
        super().__init__(master)
        self.coeficientes = tk.StringVar(value=COEFICIENTES_DEFECTO)
        self.r = tk.StringVar(value="-0.764014925")

        self.agregar_coeficientes(0)
        self.agregar_campo(1, 0, "r =", self.r)

    def ejecutar(self):
        return M.division_sintetica(
            leer_coeficientes(self.coeficientes, minimo=2),
            leer_float(self.r, "r"),
        )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Métodos Numéricos — Búsqueda de raíces")
        self.geometry("1040x700")
        self.minsize(820, 560)

        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        cabecera = ttk.Frame(self, padding=(16, 12, 16, 0))
        cabecera.pack(fill="x")
        ttk.Label(
            cabecera,
            text="Métodos numéricos para búsqueda de raíces",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            cabecera,
            text="Variable: x · Tolerancia en porcentaje · Coeficientes de mayor a menor grado",
            foreground="#555",
        ).pack(anchor="w")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        for clase in (
            TabBiseccion,
            TabMuller,
            TabNewton,
            TabBairstow,
            TabDivisionSintetica,
        ):
            notebook.add(clase(notebook), text=clase.titulo)


if __name__ == "__main__":
    App().mainloop()
