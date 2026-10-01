# ui/sistema_gestion.py

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from models.database import USUARIOS_BD

class SistemaGestion(ttk.Window):
    def __init__(self, usuario_actual, rol_actual):
        super().__init__(
            title=f"Sistema de Gestión - Usuario: {usuario_actual} ({rol_actual})",
            themename="litera",
            size=(1250, 760),
            minsize=(1000, 650)
        )
        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual

        # Datos simulados de tablas
        self.clientes_data = [("CLI-001", "Juan Pérez", "33-1234-5678", "juan@email.com", "Guadalajara")]
        self.equipos_data = [("EQ-001", "Juan Pérez", "Laptop", "Lenovo", "IdeaPad", "LNV001", "En reparación")]

        self.style.configure("Treeview", rowheight=32, font=("Arial", 10))
        self.crear_interfaz()
        self.mostrar_dashboard()

class SistemaGestion(ttk.Window):
    def __init__(self, usuario_actual, rol_actual):
        super().__init__(
            title=f"Sistema de Gestión - Usuario: {usuario_actual} ({rol_actual})",
            themename="litera",
            size=(1250, 760),
            minsize=(1000, 650)
        )

        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual

        self.clientes_data = [
            ("CLI-001", "Juan Pérez", "33-1234-5678", "juan@email.com", "Guadalajara"),
            ("CLI-002", "María López", "33-9876-5432", "maria@email.com", "Zapopan")
        ]

        self.equipos_data = [
            ("EQ-001", "Juan Pérez", "Laptop", "Lenovo", "IdeaPad", "LNV001", "En reparación"),
            ("EQ-002", "María López", "PC", "HP", "ProDesk", "HP002", "Disponible")
        ]

        self.style.configure("Treeview", rowheight=32, font=("Arial", 10))
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.crear_interfaz()
        self.mostrar_dashboard()

    # =========================================================
    # ESTRUCTURA PRINCIPAL
    # =========================================================

    def crear_interfaz(self):
        self.header = ttk.Frame(self)
        self.header.pack(fill=X)

        ttk.Separator(self.header, orient=HORIZONTAL).pack(side=BOTTOM, fill=X)

        titulo = ttk.Label(self.header, text="SISTEMA DE GESTIÓN", font=("Arial", 18, "bold"))
        titulo.pack(side=LEFT, padx=25, pady=16)

        # Corregido el bootstyle para evitar la advertencia en consola
        self.btn_usuario = ttk.Menubutton(
            self.header,
            text=f"{USUARIOS_BD[self.usuario_actual]['nombre']} ({self.rol_actual}) ▼",
            bootstyle="secondary-outline"
        )
        self.btn_usuario.pack(side=RIGHT, padx=25)

        menu_usuario = ttk.Menu(self.btn_usuario, tearoff=False)
        menu_usuario.add_command(label=f"Rol: {self.rol_actual}", state="disabled")
        menu_usuario.add_separator()
        menu_usuario.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        self.btn_usuario["menu"] = menu_usuario

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill=BOTH, expand=True)

        self.sidebar = ttk.Frame(cuerpo, width=220)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        ttk.Separator(cuerpo, orient=VERTICAL).pack(side=LEFT, fill=Y)

        self.contenido = ttk.Frame(cuerpo)
        self.contenido.pack(side=LEFT, fill=BOTH, expand=True, padx=25, pady=25)

        self.crear_menu()

    # =========================================================
    # MENÚ LATERAL Y RESTRICCIÓN POR ROL
    # =========================================================

    def crear_menu(self):
        ttk.Label(self.sidebar, text="MENÚ", font=("Arial", 11, "bold")).pack(anchor=W, padx=20, pady=(25, 15))

        opciones = [
            ("Dashboard", self.mostrar_dashboard),
            ("Clientes", self.mostrar_clientes),
            ("Equipos", self.mostrar_equipos),
            ("Órdenes", self.mostrar_ordenes),
            ("Inventario", self.mostrar_inventario),
            ("Consulta", self.mostrar_consulta),
        ]

        for texto, comando in opciones:
            if self.rol_actual == "Técnico" and texto == "Inventario":
                continue

            ttk.Button(self.sidebar, text=texto, command=comando, bootstyle="light", width=22).pack(fill=X, padx=10, pady=3)

        ttk.Separator(self.sidebar, orient=HORIZONTAL).pack(fill=X, padx=15, pady=20)

        if self.rol_actual == "Administrador":
            ttk.Button(self.sidebar, text="Configuración", command=self.mostrar_configuracion, bootstyle="light", width=22).pack(fill=X, padx=10, pady=3)

        ttk.Button(self.sidebar, text="Cerrar programa", command=self.cerrar_programa, bootstyle="light", width=22).pack(fill=X, padx=10, pady=3)

    # =========================================================
    # UTILIDADES
    # =========================================================

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def titulo_pagina(self, titulo, descripcion):
        ttk.Label(self.contenido, text=titulo, font=("Arial", 25, "bold")).pack(anchor=W)
        ttk.Label(self.contenido, text=descripcion, font=("Arial", 10)).pack(anchor=W, pady=(4, 20))

    def crear_seccion(self, titulo):
        marco = ttk.Labelframe(self.contenido, text=titulo, padding=15)
        marco.pack(fill=BOTH, expand=True, pady=(10, 0))
        return marco

    def crear_tabla(self, parent, columnas, filas, anchos=None):
        contenedor = ttk.Frame(parent)
        contenedor.pack(fill=BOTH, expand=True)

        tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")

        for i, columna in enumerate(columnas):
            tabla.heading(columna, text=columna)
            ancho = 120
            if anchos and i < len(anchos):
                ancho = anchos[i]
            tabla.column(columna, width=ancho, minwidth=70, anchor=W)

        scrollbar_y = ttk.Scrollbar(contenedor, orient=VERTICAL, command=tabla.yview)
        scrollbar_x = ttk.Scrollbar(contenedor, orient=HORIZONTAL, command=tabla.xview)
        tabla.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        tabla.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x.pack(side=BOTTOM, fill=X)

        for fila in filas:
            tabla.insert("", END, values=fila)

        return tabla

    def boton_accion(self, parent, texto, comando=None):
        return ttk.Button(parent, text=texto, command=comando, bootstyle="secondary")

    # =========================================================
    # DASHBOARD, CLIENTES, EQUIPOS, ETC. (Mantenidos igual)
    # =========================================================

    def mostrar_dashboard(self):
        self.limpiar_contenido()
        self.titulo_pagina("Dashboard", f"Resumen general del sistema (Bienvenido, {USUARIOS_BD[self.usuario_actual]['nombre']})")
        # (Omitimos el relleno visual de tarjetas para ahorrar espacio, ya está implementado en tu código base)
        self.crear_seccion("Vista general")

    def mostrar_clientes(self):
        self.limpiar_contenido()
        self.titulo_pagina("Clientes", "Administración de clientes registrados")
        barra = ttk.Frame(self.contenido)
        barra.pack(fill=X, pady=(0, 10))
        self.boton_accion(barra, "+ Nuevo cliente", lambda: messagebox.showinfo("Aviso", "Módulo de captura de cliente")).pack(side=LEFT)
        seccion = self.crear_seccion("Lista de clientes")
        self.crear_tabla(seccion, ("ID", "Nombre", "Teléfono", "Correo", "Dirección"), self.clientes_data, [100, 180, 150, 220, 160])

    def mostrar_equipos(self):
        self.limpiar_contenido()
        self.titulo_pagina("Equipos", "Registro y consulta de equipos")
        barra = ttk.Frame(self.contenido)
        barra.pack(fill=X, pady=(0, 10))
        self.boton_accion(barra, "+ Registrar equipo", lambda: messagebox.showinfo("Aviso", "Módulo de captura de equipo")).pack(side=LEFT)
        seccion = self.crear_seccion("Equipos registrados")
        self.crear_tabla(seccion, ("ID", "Cliente", "Tipo", "Marca", "Modelo", "Serie", "Estado"), self.equipos_data)

    def mostrar_ordenes(self):
        self.limpiar_contenido()
        self.titulo_pagina("Órdenes", "Gestión de órdenes de servicio")

    def mostrar_inventario(self):
        self.limpiar_contenido()
        self.titulo_pagina("Inventario", "Control de productos y refacciones")

    def mostrar_consulta(self):
        self.limpiar_contenido()
        self.titulo_pagina("Consulta", "Búsqueda general")

    # =========================================================
    # CONFIGURACIÓN: ADMINISTRACIÓN DE USUARIOS
    # =========================================================

    def mostrar_configuracion(self):
        self.limpiar_contenido()
        self.titulo_pagina("Configuración", "Administración de usuarios y roles del sistema")

        barra = ttk.Frame(self.contenido)
        barra.pack(fill=X, pady=(0, 10))

        self.boton_accion(
            barra,
            "+ Nuevo usuario",
            self.nuevo_usuario
        ).pack(side=LEFT)

        seccion = self.crear_seccion("Usuarios del sistema")

        columnas = ("Usuario", "Nombre Completo", "Rol", "Estado")
        
        # Mapeamos los datos del diccionario global a una lista de tuplas para la tabla
        filas_usuarios = []
        for username, datos in USUARIOS_BD.items():
            filas_usuarios.append((username, datos["nombre"], datos["rol"], datos["estado"]))

        self.tabla_usuarios = self.crear_tabla(
            seccion,
            columnas,
            filas_usuarios,
            [150, 250, 150, 120]
        )

    def nuevo_usuario(self):
        """Formulario de captura para nuevos usuarios"""
        ventana = ttk.Toplevel(self)
        ventana.title("Registrar Nuevo Usuario")
        ventana.geometry("400x520")
        ventana.resizable(False, False)
        ventana.place_window_center()

        ttk.Label(
            ventana,
            text="Crear Usuario",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        formulario = ttk.Frame(ventana)
        formulario.pack(fill=X, padx=30)

        ttk.Label(formulario, text="Nombre de usuario (Login) *").pack(anchor=W, pady=(5, 2))
        entry_user = ttk.Entry(formulario, width=35)
        entry_user.pack(fill=X, ipady=3)

        ttk.Label(formulario, text="Nombre completo *").pack(anchor=W, pady=(8, 2))
        entry_nombre = ttk.Entry(formulario, width=35)
        entry_nombre.pack(fill=X, ipady=3)

        ttk.Label(formulario, text="Contraseña *").pack(anchor=W, pady=(8, 2))
        entry_pass = ttk.Entry(formulario, width=35, show="*")
        entry_pass.pack(fill=X, ipady=3)

        ttk.Label(formulario, text="Rol del sistema *").pack(anchor=W, pady=(8, 2))
        combo_rol = ttk.Combobox(formulario, values=["Administrador", "Técnico", "Recepción"], state="readonly", width=33)
        combo_rol.pack(fill=X, ipady=3)
        combo_rol.current(1) # Por defecto selecciona Técnico

        def guardar_usuario():
            username = entry_user.get().strip().lower()
            nombre = entry_nombre.get().strip()
            password = entry_pass.get().strip()
            rol = combo_rol.get().strip()

            # 1. Validar campos obligatorios
            if not username or not nombre or not password or not rol:
                messagebox.showerror(
                    "Campos incompletos", 
                    "Por favor, complete todos los campos obligatorios (*).",
                    parent=ventana
                )
                return

            # 2. Validar que el usuario no exista ya en la base de datos (diccionario)
            if username in USUARIOS_BD:
                messagebox.showerror(
                    "Usuario duplicado", 
                    f"El nombre de usuario '{username}' ya está registrado en el sistema.",
                    parent=ventana
                )
                return

            # 3. Registrar el nuevo usuario en el diccionario
            USUARIOS_BD[username] = {
                "nombre": nombre,
                "password": password,
                "rol": rol,
                "estado": "Activo" # Por defecto al crear, el usuario está activo
            }

            # 4. Actualizar visualmente la tabla
            nuevo_registro = (username, nombre, rol, "Activo")
            if hasattr(self, 'tabla_usuarios'):
                self.tabla_usuarios.insert("", END, values=nuevo_registro)

            messagebox.showinfo(
                "Éxito", 
                f"Usuario '{username}' creado correctamente.",
                parent=ventana
            )
            ventana.destroy()

        ttk.Button(
            ventana,
            text="Guardar Usuario",
            command=guardar_usuario,
            bootstyle="secondary",
            width=20
        ).pack(pady=25, ipady=4)

    # =========================================================
    # MANEJO DE SESIÓN ANCLADO A SELF PARA EVITAR CRASHEOS
    # =========================================================

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de que deseas cerrar sesión?", parent=self):
            self.destroy()
            VentanaLogin().mainloop()

    def cerrar_programa(self):
        if messagebox.askyesno("Cerrar programa", "¿Estás seguro de que deseas salir del sistema?", parent=self):
            self.destroy()


# =============================================================
# VENTANA DE INICIO DE SESIÓN (LOGIN)
# =============================================================

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

        main_frame = ttk.Frame(self, padding=35)
        main_frame.pack(fill=BOTH, expand=YES)

        ttk.Label(main_frame, text="SISTEMA DE GESTIÓN", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame, text="DE EQUIPOS TECNOLOGICOS", font=("Arial", 10)).pack(pady=(0, 25))

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

        # Verificación contra el diccionario global USUARIOS_BD
        if usuario in USUARIOS_BD and USUARIOS_BD[usuario]["password"] == password:
            
            # Verificación extra: El usuario debe estar Activo
            if USUARIOS_BD[usuario]["estado"] != "Activo":
                messagebox.showerror("Acceso denegado", "Este usuario se encuentra inactivo. Contacte al administrador.")
                return

            rol = USUARIOS_BD[usuario]["rol"]
            self.destroy()

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de que deseas cerrar sesión?", parent=self):
            self.destroy()
            # Importación local para evitar dependencias circulares
            from ui.login import VentanaLogin 
            VentanaLogin().mainloop()

    def cerrar_programa(self):
        if messagebox.askyesno("Cerrar programa", "¿Estás seguro de que deseas salir del sistema?", parent=self):
            self.destroy()