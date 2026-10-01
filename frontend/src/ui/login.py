# ui/login.py

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from models.database import USUARIOS_BD

class VentanaLogin(ttk.Window):
    def __init__(self):
        super().__init__(
            title="Iniciar Sesión - Sistema de Gestión",
            themename="litera",
            size=(450, 420),
            minsize=(400, 380)
        )
        self.resizable(False, False)
        self.place_window_center()

        self.crear_widgets()

    def crear_widgets(self):
        main_frame = ttk.Frame(self, padding=35)
        main_frame.pack(fill=BOTH, expand=YES)

        ttk.Label(main_frame, text="SISTEMA DE GESTIÓN", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        
        self.entry_usuario = ttk.Entry(main_frame, width=32)
        self.entry_usuario.pack(pady=10, ipady=4)

        self.entry_password = ttk.Entry(main_frame, width=32, show="*")
        self.entry_password.pack(pady=10, ipady=4)

        ttk.Button(main_frame, text="Iniciar Sesión", bootstyle="secondary", command=self.verificar_login, width=28).pack(pady=(20, 10), ipady=4)

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip().lower()
        password = self.entry_password.get().strip()

        if usuario in USUARIOS_BD and USUARIOS_BD[usuario]["password"] == password:
            if USUARIOS_BD[usuario]["estado"] != "Activo":
                messagebox.showerror("Acceso denegado", "Usuario inactivo.")
                return

            rol = USUARIOS_BD[usuario]["rol"]
            self.destroy()
            
            # Importación local para evitar dependencias circulares
            from ui.sistema_gestion import SistemaGestion
            SistemaGestion(usuario_actual=usuario, rol_actual=rol).mainloop()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")