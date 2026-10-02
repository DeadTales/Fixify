"""parent: contenedor; columns: encabezados; height: filas visibles; retorna Treeview."""
import ttkbootstrap as ttk


def create_table(parent, columns, height=12):
    """parent: contenedor; columns: encabezados; height: filas visibles; retorna Treeview."""

    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True)

    table = ttk.Treeview(frame, columns=columns, show='headings', height=height)

    for column in columns:
        table.heading(column, text=column)
        table.column(column, anchor='center', width=130)

    scroll = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')
    return table
