from tkinter import scrolledtext, ttk


class RegistersTab:
    def __init__(self, notebook):
        self.notebook = notebook

    def Display(self):
        tab_registers = ttk.Frame(self.notebook)
        columns = ("Time", "PinID", "Value", "Type", "IsInput", "Min", "Max")
        tree = ttk.Treeview(tab_registers, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        return tab_registers

