"""Tablas legibles con desplazamiento en ambas direcciones."""
import ttkbootstrap as ttk


# Anchos en píxeles: las columnas conservan su espacio en ventanas pequeñas.
# El contenido adicional se consulta con la barra horizontal o ampliando la columna.
COLUMN_WIDTHS = {
    'ID': 80,
    'Folio': 110,
    'Nombre': 280,
    'Usuario': 240,
    'Teléfono': 160,
    'Correo': 320,
    'Rol': 150,
    'Estado': 130,
    'Tipo': 250,
    'Marca': 170,
    'Modelo': 240,
    'Nº Serie': 190,
    'Problema': 360,
    'ID Cliente': 120,
}
CENTERED_COLUMNS = {'ID', 'Folio', 'ID Cliente', 'Estado'}


def create_table(parent, columns, height=12):
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    table = ttk.Treeview(frame, columns=columns, show='headings', height=height,
                         selectmode='browse')
    for column in columns:
        anchor = 'center' if column in CENTERED_COLUMNS else 'w'
        table.heading(column, text=column, anchor=anchor)
        table.column(column, anchor=anchor, width=COLUMN_WIDTHS.get(column, 180),
                     minwidth=80, stretch=False)
    table.tag_configure('even', background='#f0f5fa')
    table.tag_configure('odd', background='#ffffff')
    vertical = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    horizontal = ttk.Scrollbar(frame, orient='horizontal', command=table.xview)
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    table.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    return table
