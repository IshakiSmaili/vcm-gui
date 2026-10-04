
from tkinter import scrolledtext, ttk
import tkinter as tk

class MonitorTab :
    def __init__ (self,notebook):
        self.notebook = notebook
        self.tab_monitor = ttk.Frame(self.notebook)
        self.text_area = scrolledtext.ScrolledText(
        self.tab_monitor,
        width=80,
        height=20,
        state='disabled',
        font=("Courier", 10))

    
    def Display (self):
        self.text_area.pack(padx=10, pady=10, expand=True, fill='both')
        return self.tab_monitor
    
    def updateTextArea(self,text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')