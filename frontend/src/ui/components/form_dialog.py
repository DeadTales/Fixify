"""Formulario genérico con validación de campos requeridos y guardado async."""
import ttkbootstrap as ttk


class FormDialog(ttk.Toplevel):
    """Formulario genérico con validación de campos requeridos y guardado async."""

    def __init__(self, master, title, fields, runner, save, on_saved, initial=None):
        """master: vista; title: título; fields: campos; runner: tareas; save/on_saved: guardar/confirmar."""
        super().__init__(master)

        self.runner, self.save, self.on_saved = runner, save, on_saved
        self.fields, self.inputs = fields, {}
        self.title(title)
        self.resizable(False, False)

        body = ttk.Frame(self, padding=28)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=title, font=('Arial', 14, 'bold')).pack(pady=(0, 15))

        for field in fields:
            ttk.Label(body, text=field.label).pack(anchor='w', pady=(5, 0))

            if field.choices:
                widget = ttk.Combobox(
                    body,
                    values=field.choices,
                    state='readonly',
                    width=38,
                )
                widget.current(0)
            else:
                widget = ttk.Entry(body, width=40, show='*' if field.secret else '')

            if initial is not None and field.name in initial:
                value = initial[field.name]
                if field.choices:
                    widget.set(value)
                else:
                    widget.insert(0, '' if value is None else str(value))
            widget.pack(fill='x', pady=5)

            self.inputs[field.name] = widget

        self.status = ttk.Label(body, text='', wraplength=350)
        self.status.pack(fill='x', pady=5)

        self.button = ttk.Button(
            body,
            text='Guardar',
            bootstyle='success',
            command=self._submit,
        )
        self.button.pack(fill='x', pady=(10, 0))
        ttk.Button(body, text='Cancelar', bootstyle='secondary-outline',
                   command=self.destroy).pack(fill='x', pady=(8, 0))
        self.bind('<Return>', lambda event: self._submit())
        self.inputs[fields[0].name].focus_set()
        self.transient(master.winfo_toplevel())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.update_idletasks()
        self.place_window_center()

    def _submit(self):
        """Lee controles en Tk; conserva espacios de contraseñas y evita doble envío."""

        if str(self.button['state']) == 'disabled':
            return

        # Las claves Field.name deben coincidir con los argumentos del service.
        # Entry entrega texto: convertir IDs explícitamente antes del service;
        # Contrato usa tipos estrictos y no convierte strings a enteros.
        values = {
            field.name: (
                self.inputs[field.name].get()
                if field.secret
                else self.inputs[field.name].get().strip()
            )
            for field in self.fields
        }
        missing = [
            field.label
            for field in self.fields
            if field.required and not values[field.name]
        ]

        if missing:
            self.status.configure(text='Complete: ' + ', '.join(missing))
            return

        self.button.configure(state='disabled')
        self.status.configure(text='Guardando…')
        self.runner.submit(self.save(values), self, self._saved, self._failed)

    def _saved(self, result):
        """result: respuesta API; notifica al módulo y cierra el formulario."""
        self.on_saved(result)
        self.destroy()

    def _failed(self, error):
        """error: fallo de solicitud; permite corregir y reintentar."""
        self.status.configure(text=str(error))
        self.button.configure(state='normal')

    def destroy(self):
        """Cancela el guardado pendiente y evita callbacks sobre un modal cerrado."""
        self.runner.cancel_owner(self)
        super().destroy()
