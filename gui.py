"""Interfaz gráfica de los métodos numéricos de búsqueda de raíces.

Flujo de la aplicación:

    Menú principal -> selección del método -> parámetros -> cálculo
    -> tabla mostrada iteración por iteración -> volver al menú.

La lógica numérica vive en ``metodos.py``; este archivo solo se ocupa de la
presentación y de la interacción con el usuario.
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

import metodos as M


FUNCION_DEFECTO = "x**4 - 4*x**3 + 2*x**2 + 3*x - 1"
COEFICIENTES_DEFECTO = "1 -4 2 3 -1"

VERDE = "#1b5e20"
ROJO = "#b71c1c"
NEUTRO = "#333333"

METODOS = (
    ("biseccion", "Bisección", "Intervalo [a, b] con cambio de signo"),
    ("muller", "Müller", "Tres aproximaciones iniciales"),
    ("newton", "Newton-Raphson", "Función y punto inicial"),
    ("bairstow", "Bairstow", "Factor cuadrático de un polinomio"),
    ("division", "División sintética", "Cociente y residuo entre (x - r)"),
)


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
        raise ValueError(
            "Los coeficientes deben ser números separados por espacios."
        ) from exc


class Tabla(ttk.Frame):
    """Tabla que va mostrando las iteraciones una por una."""

    def __init__(self, master):
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, show="headings")
        vertical = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("par", background="#f3f6fa")
        self.tree.tag_configure("impar", background="#ffffff")

        self._filas: list[list[str]] = []
        self._indice = 0

    @property
    def total(self):
        return len(self._filas)

    @property
    def mostradas(self):
        return self._indice

    @property
    def restantes(self):
        return self.total - self._indice

    def limpiar(self):
        """Vacía la tabla y reinicia el contador de iteraciones."""
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []
        self._filas = []
        self._indice = 0

    def preparar(self, resultado):
        """Carga el resultado, pero sin mostrar todavía sus filas."""
        self.limpiar()
        columnas = list(resultado.columnas)
        if not columnas:
            return

        self.tree["columns"] = columnas
        for columna in columnas:
            self.tree.heading(columna, text=columna)
            self.tree.column(
                columna, width=140, minwidth=90, anchor="center", stretch=True
            )

        self._filas = [
            [formatear(valor) for valor in fila] for fila in resultado.iteraciones
        ]

    def siguiente(self):
        """Muestra la siguiente iteración. Devuelve False si ya no hay más."""
        if self._indice >= len(self._filas):
            return False

        etiqueta = "par" if self._indice % 2 == 0 else "impar"
        item = self.tree.insert(
            "", "end", values=self._filas[self._indice], tags=(etiqueta,)
        )
        self.tree.see(item)
        self._indice += 1
        return True

    def mostrar_todas(self):
        """Revela de golpe todas las iteraciones que falten."""
        while self.siguiente():
            pass


class TabBase(ttk.Frame):
    """Base común: parámetros, controles de pausa, estado y tabla."""

    titulo = "Método"

    def __init__(self, master, al_volver):
        super().__init__(master, padding=14)
        self.al_volver = al_volver
        self.resultado = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        cabecera = ttk.Frame(self)
        cabecera.grid(row=0, column=0, sticky="ew")
        ttk.Button(cabecera, text="Volver al menú", command=self.al_volver).pack(
            side="left"
        )
        ttk.Label(
            cabecera, text=self.titulo, style="TituloMetodo.TLabel"
        ).pack(side="left", padx=14)

        ttk.Label(
            self,
            text=(
                "Variable: x · Tolerancia en porcentaje · "
                "Coeficientes de mayor a menor grado"
            ),
            style="Subtitulo.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        self.params = ttk.LabelFrame(self, text="Parámetros", padding=10)
        self.params.grid(row=2, column=0, sticky="ew")
        self.params.columnconfigure(7, weight=1)

        barra = ttk.Frame(self)
        barra.grid(row=3, column=0, sticky="ew", pady=(10, 6))
        ttk.Button(
            barra, text="Calcular", style="Accion.TButton", command=self.calcular
        ).pack(side="left")
        self.btn_siguiente = ttk.Button(
            barra,
            text="Siguiente iteración",
            command=self.siguiente,
            state="disabled",
        )
        self.btn_siguiente.pack(side="left", padx=(8, 0))
        self.btn_todas = ttk.Button(
            barra, text="Mostrar todas", command=self.mostrar_todas, state="disabled"
        )
        self.btn_todas.pack(side="left", padx=(8, 0))
        self.progreso = ttk.Label(barra, text="")
        self.progreso.pack(side="right")

        self.estado = ttk.Label(
            self, text="Introduce los datos y pulsa Calcular.", wraplength=960
        )
        self.estado.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.tabla = Tabla(self)
        self.tabla.grid(row=5, column=0, sticky="nsew")

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
        self.resultado = None
        self.tabla.limpiar()
        self._desactivar_controles()
        self.progreso.configure(text="")

        try:
            resultado = self.ejecutar()
            self.tabla.preparar(resultado)
        except Exception as exc:
            self.estado.configure(text=str(exc), foreground=ROJO)
            messagebox.showerror("No se pudo calcular", str(exc))
            return

        self.resultado = resultado

        if self.tabla.total == 0:
            self._finalizar()
            return

        # La primera iteración se muestra de inmediato; las demás esperan
        # a que el usuario pulse «Siguiente iteración».
        self.tabla.siguiente()
        self._actualizar_controles()

    def siguiente(self):
        if self.resultado is None:
            return
        if self.tabla.siguiente():
            self._actualizar_controles()

    def mostrar_todas(self):
        if self.resultado is None:
            return
        self.tabla.mostrar_todas()
        self._actualizar_controles()

    def _desactivar_controles(self):
        self.btn_siguiente.state(["disabled"])
        self.btn_todas.state(["disabled"])

    def _actualizar_controles(self):
        if self.resultado is None:
            return

        mostradas = self.tabla.mostradas
        total = self.tabla.total
        self.progreso.configure(text=f"{mostradas} de {total} iteraciones")

        if self.tabla.restantes:
            self.btn_siguiente.state(["!disabled"])
            self.btn_todas.state(["!disabled"])
            self.btn_siguiente.configure(
                text=f"Siguiente iteración ({mostradas + 1}/{total})"
            )
            self.estado.configure(
                text=(
                    f"Mostrando la iteración {mostradas} de {total}. "
                    "Pulsa «Siguiente iteración» para continuar."
                ),
                foreground=NEUTRO,
            )
            self.btn_siguiente.focus_set()
        else:
            self._finalizar()

    def _finalizar(self):
        total = self.tabla.total
        self.progreso.configure(text=f"{total} de {total} iteraciones")
        self._desactivar_controles()
        self.btn_siguiente.configure(text="Siguiente iteración")

        mensaje = ""
        if self.resultado is not None:
            mensaje = self.resultado.mensaje
        self.estado.configure(
            text=mensaje or "Cálculo completado.",
            foreground=(
                VERDE
                if self.resultado is not None and self.resultado.convergio
                else ROJO
            ),
        )

    def ejecutar(self):  # pragma: no cover - implementado en cada pestaña
        raise NotImplementedError


class TabBiseccion(TabBase):
    titulo = "Bisección"

    def __init__(self, master, al_volver):
        super().__init__(master, al_volver)
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

    def __init__(self, master, al_volver):
        super().__init__(master, al_volver)
        self.funcion = tk.StringVar(value=FUNCION_DEFECTO)
        self.x0 = tk.StringVar(value="0")
        self.x1 = tk.StringVar(value="0.5")
        self.x2 = tk.StringVar(value="1")
        self.tol = tk.StringVar(value="1e-6")
        self.max_iter = tk.StringVar(value="100")

        self.agregar_funcion(0)
        self.agregar_campo(1, 0, "x0 =", self.x0)
        self.agregar_campo(1, 1, "x1 =", self.x1)
        self.agregar_campo(1, 2, "x2 =", self.x2)
        self.agregar_campo(2, 0, "Tolerancia (%) =", self.tol)
        self.agregar_campo(2, 1, "Máx. iteraciones =", self.max_iter)

    def ejecutar(self):
        return M.muller(
            leer_float(self.x0, "x0"),
            leer_float(self.x1, "x1"),
            leer_float(self.x2, "x2"),
            max_iter=leer_entero(self.max_iter, "el máximo de iteraciones"),
            tol=leer_float(self.tol, "la tolerancia"),
            f=self.funcion.get(),
        )


class TabNewton(TabBase):
    titulo = "Newton-Raphson"

    def __init__(self, master, al_volver):
        super().__init__(master, al_volver)
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

    def __init__(self, master, al_volver):
        super().__init__(master, al_volver)
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

    def __init__(self, master, al_volver):
        super().__init__(master, al_volver)
        self.coeficientes = tk.StringVar(value=COEFICIENTES_DEFECTO)
        self.r = tk.StringVar(value="-0.764014925")

        self.agregar_coeficientes(0)
        self.agregar_campo(1, 0, "r =", self.r)

    def ejecutar(self):
        return M.division_sintetica(
            leer_coeficientes(self.coeficientes, minimo=2),
            leer_float(self.r, "r"),
        )


class MenuPrincipal(ttk.Frame):
    """Pantalla de inicio con la selección de método y la opción Salir."""

    def __init__(self, master, al_seleccionar, al_salir):
        super().__init__(master, padding=40)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        caja = ttk.Frame(self)
        caja.grid(row=0, column=0)

        ttk.Label(
            caja, text="Métodos Numéricos", style="TituloMenu.TLabel"
        ).pack()
        ttk.Label(
            caja,
            text="Búsqueda de raíces de ecuaciones",
            style="SubtituloMenu.TLabel",
        ).pack(pady=(2, 24))

        for indice, (clave, titulo, descripcion) in enumerate(METODOS, start=1):
            fila = ttk.Frame(caja)
            fila.pack(fill="x", pady=3)

            ttk.Button(
                fila,
                text=f"{indice}.  {titulo}",
                width=28,
                style="Menu.TButton",
                command=lambda c=clave: al_seleccionar(c),
            ).pack(side="left")
            ttk.Label(
                fila, text=descripcion, style="Descripcion.TLabel"
            ).pack(side="left", padx=(14, 0))

        ttk.Separator(caja).pack(fill="x", pady=14)
        ttk.Button(
            caja,
            text="0.  Salir",
            width=28,
            style="Salir.TButton",
            command=al_salir,
        ).pack(fill="x")

        ttk.Label(
            caja,
            text="Selecciona un método para introducir sus parámetros.",
            style="Descripcion.TLabel",
        ).pack(pady=(18, 0))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Métodos Numéricos — Menú principal")
        self.geometry("1100x720")
        self.minsize(920, 600)
        self.protocol("WM_DELETE_WINDOW", self.salir)

        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("TituloMenu.TLabel", font=("TkDefaultFont", 24, "bold"))
        estilo.configure(
            "SubtituloMenu.TLabel", font=("TkDefaultFont", 12), foreground="#555555"
        )
        estilo.configure("TituloMetodo.TLabel", font=("TkDefaultFont", 16, "bold"))
        estilo.configure("Subtitulo.TLabel", foreground="#555555")
        estilo.configure("Descripcion.TLabel", foreground="#555555")
        estilo.configure("Menu.TButton", font=("TkDefaultFont", 11), padding=(10, 7))
        estilo.configure(
            "Accion.TButton", font=("TkDefaultFont", 10, "bold"), padding=(12, 5)
        )
        estilo.configure(
            "Salir.TButton",
            font=("TkDefaultFont", 11),
            padding=(10, 7),
            foreground=ROJO,
        )

        self.pantalla_actual = "menu"
        self.pantallas = {}

        self.contenedor = ttk.Frame(self)
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.rowconfigure(0, weight=1)
        self.contenedor.columnconfigure(0, weight=1)

        self.pantallas["menu"] = MenuPrincipal(
            self.contenedor,
            al_seleccionar=self.mostrar_metodo,
            al_salir=self.salir,
        )
        for clave, clase in (
            ("biseccion", TabBiseccion),
            ("muller", TabMuller),
            ("newton", TabNewton),
            ("bairstow", TabBairstow),
            ("division", TabDivisionSintetica),
        ):
            self.pantallas[clave] = clase(self.contenedor, al_volver=self.mostrar_menu)

        for pantalla in self.pantallas.values():
            pantalla.grid(row=0, column=0, sticky="nsew")

        self.mostrar_menu()

    def mostrar_menu(self):
        self.pantalla_actual = "menu"
        self.pantallas["menu"].tkraise()
        self.title("Métodos Numéricos — Menú principal")

    def mostrar_metodo(self, clave):
        pantalla = self.pantallas.get(clave)
        if pantalla is None:
            return
        self.pantalla_actual = clave
        pantalla.tkraise()
        self.title(f"Métodos Numéricos — {pantalla.titulo}")

    def salir(self):
        if messagebox.askyesno("Salir", "¿Deseas cerrar el programa?"):
            self.destroy()


if __name__ == "__main__":
    App().mainloop()
