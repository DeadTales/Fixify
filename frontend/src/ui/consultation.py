"""Ventana pública para verificar el estado de una reparación."""
import ttkbootstrap as ttk


class ConsultationDialog(ttk.Toplevel):
    """Consulta por folio y teléfono sin exponer el panel de empleados."""

    def __init__(self, master, service, runner):
        super().__init__(master)
        self.service = service
        self.runner = runner
        self.title('Consultar reparación')
        self.resizable(False, False)
        self.transient(master)
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        body = ttk.Frame(self, padding=28)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Estado de tu reparación', font=('Arial', 16, 'bold')).pack(
            anchor='w', pady=(0, 5)
        )
        ttk.Label(body, text='Ingresa el folio y el teléfono registrado.',
                  bootstyle='secondary').pack(anchor='w', pady=(0, 16))
        ttk.Label(body, text='Folio').pack(anchor='w')
        self.folio = ttk.Entry(body, width=42)
        self.folio.pack(fill='x', pady=(4, 12))
        ttk.Label(body, text='Teléfono').pack(anchor='w')
        self.phone = ttk.Entry(body)
        self.phone.pack(fill='x', pady=(4, 12))
        self.status = ttk.Label(body, text='', wraplength=360, justify='left')
        self.status.pack(fill='x', pady=8)
        self.button = ttk.Button(body, text='Consultar', command=self.submit)
        self.button.pack(fill='x', pady=(8, 5))
        ttk.Button(body, text='Cerrar', bootstyle='secondary-outline',
                   command=self.destroy).pack(fill='x')
        self.bind('<Return>', lambda _event: self.submit())
        self.folio.focus_set()
        self.update_idletasks()
        self.place_window_center()

    def submit(self):
        if str(self.button['state']) == 'disabled':
            return
        folio, phone = self.folio.get().strip(), self.phone.get().strip()
        if not folio or not phone:
            self.status.configure(text='Complete folio y teléfono.')
            return
        self.button.configure(state='disabled')
        self.status.configure(text='Consultando…')
        self.runner.submit(self.service.consultar(folio, phone), self,
                           self._show_result, self._show_error)

    def _show_result(self, result):
        updated = result.actualizadoEn.astimezone().strftime('%d/%m/%Y %H:%M')
        self.status.configure(
            text=f'Folio: {result.folio}\nEquipo: {result.equipo}\n'
                 f'Estado: {result.estado}\nActualizado: {updated}',
            bootstyle='success',
        )
        self.button.configure(state='normal')

    def _show_error(self, error):
        self.status.configure(text=str(error), bootstyle='danger')
        self.button.configure(state='normal')

    def destroy(self):
        self.runner.cancel_owner(self)
        super().destroy()
