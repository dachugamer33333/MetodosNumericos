import tkinter as tk
from tkinter import ttk, messagebox

root = tk.Tk()
root.title("Mi primera app")
root.geometry("300x200")

nombre = tk.StringVar()

def saludar():
    messagebox.showinfo("Hola", f"Hola, {nombre.get()}!")

ttk.Label(root, text="Tu nombre:").pack(pady=10)
ttk.Entry(root, textvariable=nombre).pack()
ttk.Button(root, text="Saludar", command=saludar).pack(pady=10)

root.mainloop()