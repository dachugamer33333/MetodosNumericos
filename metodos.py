from sympy import *
import math as mt
import cmath as cm

def funcion(x):
    return x**4 - 4*(x**3) + 2*(x**2) + 3*x -1

def error_relativo(actual, anterior):
    return abs((actual - anterior) / actual) * 100

def biseccion(a, b, tol=1e-6, max_iter=100):
    if funcion(a) * funcion(b) >= 0:
        print("El intervalo no tiene cambio de signo, no aplica bisección")
        return None

    pn_anterior = a
    for i in range(1, max_iter + 1):
        pn = (a + b) / 2

        if funcion(a) * funcion(pn) < 0:
            b = pn
        else:
            a = pn

        err = error_relativo(pn, pn_anterior) if pn != 0 else 0
        print(f"iter {i}: pn = {pn:.8f}, error = {err:.6f}%")

        if funcion(pn) == 0 or err < tol:
            return pn
        pn_anterior = pn

    return pn
import cmath as cm

def muller(a, b, c, max_iter, tol=1e-8):
    print(f"{'Iter':<5}{'Raiz':<30}{'Error':<15}")
    d = c
    for i in range(1, max_iter + 1):
        h0 = b - a
        h1 = c - b
        delta_0 = (funcion(b) - funcion(a)) / h0
        delta_1 = (funcion(c) - funcion(b)) / h1

        A = (delta_1 - delta_0) / (h1 + h0)
        B = A * h1 + delta_1
        C = funcion(c)

        disc = cm.sqrt(B**2 - 4*A*C)

        # Elegir el signo que maximiza |denominador|
        if abs(B + disc) > abs(B - disc):
            den = B + disc
        else:
            den = B - disc

        d = c - (2*C) / den
        error = abs(d - c) / abs(d) if d != 0 else abs(d - c)

        print(f"{i:<5}{str(d):<30}{error:<15.8f}")

        if error < tol:
            return d

        a, b, c = b, c, d

    return d

    

#raiz = biseccion(-1, 0)
#print("Raíz aproximada:", raiz)

raiz = muller(0,0.5,1,3)
print("Raíz aproximada:", raiz)