import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from services.api_service import api_client

class SistemaGestion(ttk.Toplevel):
    def __init__(self, master=None, usuario_actual="Invitado", rol_actual="invitado", token=None):
        super().__init__(master)
        self.master = master
        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual
        self.token = token
        
        if self.token:
            api_client.set_token(self.token)

        self.title("Sistema de Gestión de Equipos Tecnológicos - Fixify")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.place_window_center()

        self.crear_layout()
        self.mostrar_dashboard()

    def cerrar_aplicacion(self):
        self.destroy()
        if self.master:
            self.master.destroy()

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea salir del sistema?"):
            self.destroy()
            if self.master:
                self.master.deiconify()

    def crear_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ttk.Frame(self, bootstyle="secondary", padding=15)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        lbl_titulo = ttk.Label(self.sidebar, text="FIXIFY", font=("Arial", 18, "bold"), bootstyle="inverse-secondary")
        lbl_titulo.pack(pady=(10, 20), anchor="w")

        info_user = f"Usuario: {self.usuario_actual.upper()}\nRol: {self.rol_actual}"
        lbl_user = ttk.Label(self.sidebar, text=info_user, font=("Arial", 9), bootstyle="inverse-secondary")
        lbl_user.pack(pady=(0, 25), anchor="w")

        btn_dash = ttk.Button(self.sidebar, text="📊  Dashboard", bootstyle="secondary", command=self.mostrar_dashboard, width=18)
        btn_dash.pack(pady=5, fill=X)

        btn_equipos = ttk.Button(self.sidebar, text="💻  Equipos", bootstyle="secondary", command=self.mostrar_equipos, width=18)
        btn_equipos.pack(pady=5, fill=X)

        btn_clientes = ttk.Button(self.sidebar, text="👥  Clientes", bootstyle="secondary", command=self.mostrar_clientes, width=18)
        btn_clientes.pack(pady=5, fill=X)

        if self.rol_actual.lower() in ["administrador", "admin"]:
            btn_config = ttk.Button(self.sidebar, text="⚙️  Configuración", bootstyle="secondary", command=self.mostrar_configuracion, width=18)
            btn_config.pack(pady=5, fill=X)

        frame_bottom = ttk.Frame(self.sidebar, bootstyle="secondary")
        frame_bottom.pack(side=BOTTOM, fill=X, pady=10)

        btn_logout = ttk.Button(frame_bottom, text="🚪  Cerrar Sesión", bootstyle="danger", command=self.cerrar_sesion, width=18)
        btn_logout.pack(fill=X)

        self.content_area = ttk.Frame(self, padding=25)
        self.content_area.grid(row=0, column=1, sticky="nsew")

    def limpiar_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def crear_encabezado(self, titulo):
        lbl = ttk.Label(self.content_area, text=titulo, font=("Arial", 18, "bold"))
        lbl.pack(anchor="w", pady=(0, 20))

    # --- DASHBOARD DINÁMICO ---
    def mostrar_dashboard(self):
        self.limpiar_contenido()
        self.crear_encabezado("Dashboard General")

        # Consultamos datos reales a la base de datos
        exito_eq, equipos = api_client.obtener_equipos()
        exito_cli, clientes = api_client.obtener_clientes()
        exito_usr, usuarios = api_client.obtener_usuarios()

        total_equipos = len(equipos) if (exito_eq and isinstance(equipos, list)) else 0
        total_clientes = len(clientes) if (exito_cli and isinstance(clientes, list)) else 0
        total_usuarios = len(usuarios) if (exito_usr and isinstance(usuarios, list)) else 0

        frame_cards = ttk.Frame(self.content_area)
        frame_cards.pack(fill=X, pady=(0, 20))

        # Tarjetas dinámicas que incrementan en tiempo real
        self.crear_tarjeta(frame_cards, "Total Equipos", str(total_equipos), "info", 0)
        self.crear_tarjeta(frame_cards, "Clientes Registrados", str(total_clientes), "success", 1)
        self.crear_tarjeta(frame_cards, "Usuarios / Personal", str(total_usuarios), "primary", 2)

        lbl_recent = ttk.Label(self.content_area, text="Últimos Equipos Registrados", font=("Arial", 12, "bold"))
        lbl_recent.pack(anchor="w", pady=(10, 10))

        cols = ("Folio", "Tipo", "Marca", "Modelo", "Problema", "ID Cliente")
        tabla = ttk.Treeview(self.content_area, columns=cols, show="headings", height=8)
        for col in cols:
            tabla.heading(col, text=col)
            tabla.column(col, anchor=CENTER, width=130)
        tabla.pack(fill=BOTH, expand=YES)

        # Cargar actividades recientes
        if exito_eq and isinstance(equipos, list):
            for eq in reversed(equipos[-8:]):
                folio = f"EQ-{eq.get('id', 0):03d}"
                tabla.insert("", END, values=(
                    folio,
                    eq.get("tipo", ""),
                    eq.get("marca", ""),
                    eq.get("modelo", ""),
                    eq.get("problema_reportado", ""),
                    eq.get("client_id", "")
                ))

    def crear_tarjeta(self, parent, titulo, valor, estilo, col):
        card = ttk.Labelframe(parent, text=titulo, bootstyle=estilo, padding=15)
        card.grid(row=0, column=col, padx=10, pady=5, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        lbl_val = ttk.Label(card, text=valor, font=("Arial", 22, "bold"))
        lbl_val.pack()

    # --- SECCIÓN EQUIPOS ---
    def mostrar_equipos(self):
        self.limpiar_contenido()
        self.crear_encabezado("Gestión de Equipos")

        frame_top = ttk.Frame(self.content_area)
        frame_top.pack(fill=X, pady=(0, 15))

        if self.rol_actual.lower() in ["administrador", "admin", "recepción", "recepcion"]:
            ttk.Button(frame_top, text="+ Registrar Equipo", bootstyle="success", command=self.modal_nuevo_equipo).pack(side=RIGHT)

        cols = ("Folio", "Tipo", "Marca", "Modelo", "Nº Serie", "Problema Reportado", "ID Cliente")
        self.tabla_equipos = ttk.Treeview(self.content_area, columns=cols, show="headings", height=12)
        for col in cols:
            self.tabla_equipos.heading(col, text=col)
            self.tabla_equipos.column(col, anchor=CENTER, width=120)
        self.tabla_equipos.pack(fill=BOTH, expand=YES)

        self.cargar_equipos()

    def cargar_equipos(self):
        for item in self.tabla_equipos.get_children():
            self.tabla_equipos.delete(item)

        exito, data = api_client.obtener_equipos()
        if exito and isinstance(data, list):
            for eq in data:
                folio = f"EQ-{eq.get('id', 0):03d}"
                self.tabla_equipos.insert("", END, values=(
                    folio,
                    eq.get("tipo", ""),
                    eq.get("marca", ""),
                    eq.get("modelo", ""),
                    eq.get("numero_serie") or "-",
                    eq.get("problema_reportado", ""),
                    eq.get("client_id", "")
                ))
        elif not exito:
            messagebox.showerror("Error", str(data))

    # --- SECCIÓN CLIENTES (VISUALIZACIÓN CORREGIDA) ---
    def mostrar_clientes(self):
        self.limpiar_contenido()
        self.crear_encabezado("Directorio de Clientes")

        frame_top = ttk.Frame(self.content_area)
        frame_top.pack(fill=X, pady=(0, 15))

        if self.rol_actual.lower() in ["administrador", "admin", "recepción", "recepcion"]:
            ttk.Button(frame_top, text="+ Nuevo Cliente", bootstyle="success", command=self.modal_nuevo_cliente).pack(side=RIGHT)

        cols = ("ID", "Nombre", "Teléfono", "Correo Electrónico", "Dirección")
        self.tabla_clientes = ttk.Treeview(self.content_area, columns=cols, show="headings", height=12)
        for col in cols:
            self.tabla_clientes.heading(col, text=col)
            self.tabla_clientes.column(col, anchor=CENTER, width=150)
        self.tabla_clientes.pack(fill=BOTH, expand=YES)

        self.cargar_clientes()

    def cargar_clientes(self):
        for item in self.tabla_clientes.get_children():
            self.tabla_clientes.delete(item)
            
        exito, data = api_client.obtener_clientes()
        if exito and isinstance(data, list):
            for c in data:
                self.tabla_clientes.insert("", END, values=(
                    c.get("id", ""),
                    c.get("nombre", ""),
                    c.get("telefono", ""),
                    c.get("correo") or "-",
                    c.get("direccion") or "-"
                ))
        elif not exito:
            messagebox.showerror("Error", str(data))

    # --- SECCIÓN CONFIGURACIÓN / USUARIOS ---
    def mostrar_configuracion(self):
        self.limpiar_contenido()
        self.crear_encabezado("Configuración del Sistema")

        frame_top = ttk.Frame(self.content_area)
        frame_top.pack(fill=X, pady=(0, 15))

        ttk.Button(frame_top, text="+ Nuevo Usuario", bootstyle="success", command=self.modal_nuevo_usuario).pack(side=RIGHT)

        cols = ("ID", "Usuario", "Rol", "Estado")
        self.tabla_usuarios = ttk.Treeview(self.content_area, columns=cols, show="headings", height=10)
        for col in cols:
            self.tabla_usuarios.heading(col, text=col)
            self.tabla_usuarios.column(col, anchor=CENTER, width=150)
        self.tabla_usuarios.pack(fill=BOTH, expand=YES)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        for item in self.tabla_usuarios.get_children():
            self.tabla_usuarios.delete(item)

        exito, data = api_client.obtener_usuarios()
        if exito and isinstance(data, list):
            for u in data:
                self.tabla_usuarios.insert("", END, values=(
                    u.get("id", ""),
                    u.get("username", ""),
                    u.get("role", ""),
                    "Activo" if u.get("is_active", True) else "Inactivo"
                ))

    # --- MODALES DE REGISTRO ---
    def modal_nuevo_cliente(self):
        ventana = ttk.Toplevel(self)
        ventana.title("Nuevo Cliente")
        ventana.geometry("400x420")
        ventana.place_window_center()

        ttk.Label(ventana, text="Registrar Cliente", font=("Arial", 14, "bold")).pack(pady=15)

        ttk.Label(ventana, text="Nombre Completo:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_nombre = ttk.Entry(ventana, width=35)
        entry_nombre.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Teléfono:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_tel = ttk.Entry(ventana, width=35)
        entry_tel.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Correo Electrónico:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_correo = ttk.Entry(ventana, width=35)
        entry_correo.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Dirección:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_dir = ttk.Entry(ventana, width=35)
        entry_dir.pack(padx=20, pady=5)

        def guardar():
            nombre = entry_nombre.get().strip()
            tel = entry_tel.get().strip()
            correo = entry_correo.get().strip()
            dir_val = entry_dir.get().strip()

            if not nombre or not tel:
                messagebox.showerror("Error", "Nombre y Teléfono son obligatorios.", parent=ventana)
                return

            exito, data = api_client.crear_cliente(nombre, tel, correo, dir_val)
            if exito:
                messagebox.showinfo("Éxito", "Cliente creado correctamente.", parent=ventana)
                ventana.destroy()
                self.cargar_clientes()
            else:
                messagebox.showerror("Error", str(data), parent=ventana)

        ttk.Button(ventana, text="Guardar Cliente", bootstyle="success", command=guardar).pack(pady=20)

    def modal_nuevo_equipo(self):
        # Obtener lista de clientes para selector interactivo
        exito, clientes = api_client.obtener_clientes()
        if not exito or not isinstance(clientes, list) or len(clientes) == 0:
            messagebox.showwarning("Atención", "Debe registrar al menos un cliente antes de ingresar un equipo.")
            return

        mapa_clientes = {f"[{c['id']}] {c['nombre']} ({c['telefono']})": c['id'] for c in clientes}

        ventana = ttk.Toplevel(self)
        ventana.title("Registrar Equipo")
        ventana.geometry("420x540")
        ventana.place_window_center()

        ttk.Label(ventana, text="Nuevo Equipo", font=("Arial", 14, "bold")).pack(pady=15)

        ttk.Label(ventana, text="Seleccionar Cliente:").pack(anchor="w", padx=20, pady=(5, 0))
        cb_cliente = ttk.Combobox(ventana, values=list(mapa_clientes.keys()), state="readonly", width=38)
        cb_cliente.current(0)
        cb_cliente.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Tipo de Equipo (ej. Laptop, Teléfono):").pack(anchor="w", padx=20, pady=(5, 0))
        entry_tipo = ttk.Entry(ventana, width=40)
        entry_tipo.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Marca:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_marca = ttk.Entry(ventana, width=40)
        entry_marca.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Modelo:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_modelo = ttk.Entry(ventana, width=40)
        entry_modelo.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Número de Serie (Opcional):").pack(anchor="w", padx=20, pady=(5, 0))
        entry_serie = ttk.Entry(ventana, width=40)
        entry_serie.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Problema Reportado:").pack(anchor="w", padx=20, pady=(5, 0))
        entry_prob = ttk.Entry(ventana, width=40)
        entry_prob.pack(padx=20, pady=5)

        def guardar():
            cliente_str = cb_cliente.get()
            client_id = mapa_clientes.get(cliente_str)
            tipo = entry_tipo.get().strip()
            marca = entry_marca.get().strip()
            modelo = entry_modelo.get().strip()
            serie = entry_serie.get().strip()
            prob = entry_prob.get().strip()

            if not client_id or not tipo or not marca or not modelo or not prob:
                messagebox.showerror("Error", "Por favor complete todos los campos requeridos.", parent=ventana)
                return

            exito, data = api_client.crear_equipo(tipo, marca, modelo, prob, client_id, serie)
            if exito:
                folio = data.get("folio", "")
                messagebox.showinfo("Éxito", f"Equipo registrado exitosamente.\nFolio: {folio}", parent=ventana)
                ventana.destroy()
                self.mostrar_equipos()
            else:
                messagebox.showerror("Error", str(data), parent=ventana)

        ttk.Button(ventana, text="Registrar Equipo", bootstyle="success", command=guardar).pack(pady=20)

    def modal_nuevo_usuario(self):
        ventana = ttk.Toplevel(self)
        ventana.title("Nuevo Usuario")
        ventana.geometry("400x380")
        ventana.place_window_center()

        ttk.Label(ventana, text="Crear Nuevo Usuario", font=("Arial", 14, "bold")).pack(pady=15)

        ttk.Label(ventana, text="Nombre de usuario (Username):").pack(anchor="w", padx=20, pady=(5, 0))
        entry_user = ttk.Entry(ventana, width=35)
        entry_user.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Contraseña (mín. 6 caracteres):").pack(anchor="w", padx=20, pady=(5, 0))
        entry_pass = ttk.Entry(ventana, width=35, show="*")
        entry_pass.pack(padx=20, pady=5)

        ttk.Label(ventana, text="Rol del Usuario:").pack(anchor="w", padx=20, pady=(5, 0))
        cb_rol = ttk.Combobox(ventana, values=["Administrador", "Técnico", "Recepción"], state="readonly", width=33)
        cb_rol.set("Técnico")
        cb_rol.pack(padx=20, pady=5)

        def guardar():
            username = entry_user.get().strip()
            password = entry_pass.get().strip()
            rol_ui = cb_rol.get()

            mapa_roles_inv = {
                "Administrador": "admin",
                "Técnico": "tecnico",
                "Recepción": "recepcion"
            }
            role_backend = mapa_roles_inv.get(rol_ui, "tecnico")

            if not username or not password:
                messagebox.showerror("Error", "Nombre de usuario y contraseña son requeridos.", parent=ventana)
                return

            exito, data = api_client.crear_usuario(username, password, role_backend)
            if exito:
                messagebox.showinfo("Éxito", "Usuario creado con éxito.", parent=ventana)
                ventana.destroy()
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", str(data), parent=ventana)

        ttk.Button(ventana, text="Crear Usuario", bootstyle="success", command=guardar).pack(pady=20)