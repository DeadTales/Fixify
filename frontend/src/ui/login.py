import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from services.api_service import api_client

class VentanaLogin(ttk.Window):
    def __init__(self):
        super().__init__(
            title="Iniciar Sesión - Sistema de Gestión",
            themename="litera",
            size=(450, 460),
            minsize=(400, 450)
        )
        self.resizable(False, False)
        self.place_window_center()

        self.crear_widgets()

    def crear_widgets(self):
        main_frame = ttk.Frame(self, padding=35)
        main_frame.pack(fill=BOTH, expand=YES)

        ttk.Label(main_frame, text="SISTEMA DE GESTIÓN", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame, text="DE EQUIPOS TECNOLÓGICOS", font=("Arial", 10)).pack(pady=(0, 25))
        
        self.entry_usuario = ttk.Entry(main_frame, width=32)
        self.entry_usuario.insert(0, "USUARIO")
        self.entry_usuario.pack(pady=10, ipady=4)
        self.entry_usuario.bind("<FocusIn>", lambda e: self.quitar_placeholder(self.entry_usuario, "USUARIO"))
        self.entry_usuario.bind("<FocusOut>", lambda e: self.poner_placeholder(self.entry_usuario, "USUARIO"))

        self.entry_password = ttk.Entry(main_frame, width=32)
        self.entry_password.insert(0, "CONTRASEÑA")
        self.entry_password.pack(pady=10, ipady=4)
        self.entry_password.bind("<FocusIn>", lambda e: self.activar_password_mode(self.entry_password, "CONTRASEÑA"))
        self.entry_password.bind("<FocusOut>", lambda e: self.poner_placeholder_pass(self.entry_password, "CONTRASEÑA"))

        ttk.Button(
            main_frame, 
            text="Iniciar Sesión", 
            bootstyle="secondary", 
            command=self.verificar_login, 
            width=28
        ).pack(pady=(20, 10), ipady=4)

        ttk.Button(
            main_frame, 
            text="¿Olvidaste tu contraseña?", 
            bootstyle="link", 
            command=self.mostrar_recuperacion
        ).pack(pady=(5, 0))

    def quitar_placeholder(self, entry, texto):
        if entry.get() == texto:
            entry.delete(0, END)

    def poner_placeholder(self, entry, texto):
        if not entry.get():
            entry.insert(0, texto)

    def activar_password_mode(self, entry, texto):
        if entry.get() == texto:
            entry.delete(0, END)
            entry.config(show="*")

    def poner_placeholder_pass(self, entry, texto):
        if not entry.get():
            entry.config(show="")
            entry.insert(0, texto)

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip().lower()
        password = self.entry_password.get().strip()

        if not usuario or usuario == "USUARIO" or not password or password == "CONTRASEÑA":
            messagebox.showerror("Error de acceso", "Por favor, complete los campos de usuario y contraseña.")
            return

        exito, data = api_client.login(usuario, password)

        if exito:
            token = data.get("access_token")
            rol_backend = data.get("role", "tecnico")
            
            mapa_roles = {
                "admin": "Administrador",
                "tecnico": "Técnico",
                "recepcion": "Recepción"
            }
            rol_display = mapa_roles.get(rol_backend, rol_backend.capitalize())

            self.withdraw()
            
            self.entry_usuario.delete(0, 'end')
            self.poner_placeholder(self.entry_usuario, "USUARIO")
            self.entry_password.delete(0, 'end')
            self.poner_placeholder_pass(self.entry_password, "CONTRASEÑA")
            self.focus_set()
            
            from ui.sistema_gestion import SistemaGestion
            SistemaGestion(master=self, usuario_actual=usuario, rol_actual=rol_display, token=token)
        else:
            messagebox.showerror("Acceso denegado", str(data))

    def mostrar_recuperacion(self):
        ventana = ttk.Toplevel(self)
        ventana.title("Recuperar Cuenta")
        ventana.geometry("480x280")
        ventana.resizable(False, False)
        ventana.place_window_center()

        ttk.Label(ventana, text="Recuperación de Cuenta", font=("Arial", 16, "bold")).pack(pady=(20, 10))

        mensaje = (
            "Si no recuerdas tu contraseña o necesitas acceso al sistema, "
            "contacta al administrador de la plataforma para restablecer tu cuenta."
        )
        ttk.Label(ventana, text=mensaje, wraplength=400, justify=CENTER).pack(pady=20)

        ttk.Button(
            ventana, 
            text="Entendido", 
            bootstyle="secondary", 
            command=ventana.destroy, 
            width=20
        ).pack(pady=10)