import tkinter as tk
from tkinter import ttk


class PinsTab:
    def __init__(self, notebook):
        self.notebook = notebook

        # =================================================
        # Pin data
        # =================================================

        self.pin_values = {}

        # =================================================
        # Register types
        # =================================================

        self.register_type_names = {
            0x01: "Digital Input",
            0x02: "Digital Output",
            0x03: "Analog Input",
            0x04: "Analog Output",
            0x05: "PWM Output",
            0x06: "Special Function",
        }

        # =================================================
        # Columns
        # =================================================

        self.pin_columns = (
            "PinID",
            "Value",
            "Register Type",
            "Read Only",
            "Min",
            "Max",
        )

        # =================================================
        # Tab
        # =================================================

        self.tab_pins = ttk.Frame(self.notebook)

        # =================================================
        # Header
        # =================================================

        self.header_frame = ttk.Frame(self.tab_pins)

        self.timer_label_title = ttk.Label(
            self.header_frame,
            text="Time:",
        )

        self.timer_label = ttk.Label(
            self.header_frame,
            text="00:00:000",
            font=("Arial", 12, "bold"),
        )

        # =================================================
        # Tree
        # =================================================

        self.pin_tree = ttk.Treeview(
            self.tab_pins,
            columns=self.pin_columns,
            show="headings",
        )

    # =====================================================
    # DISPLAY
    # =====================================================

    def Display(self):
        # Header
        self.header_frame.pack(
            fill="x",
            padx=10,
            pady=5,
        )

        self.timer_label_title.pack(side="left")

        self.timer_label.pack(
            side="left",
            padx=5,
        )

        # Columns
        for column in self.pin_columns:
            self.pin_tree.heading(
                column,
                text=column,
            )

        self.pin_tree.column(
            "PinID",
            width=80,
            anchor="center",
        )

        self.pin_tree.column(
            "Value",
            width=100,
            anchor="center",
        )

        self.pin_tree.column(
            "Register Type",
            width=160,
            anchor="center",
        )

        self.pin_tree.column(
            "Read Only",
            width=100,
            anchor="center",
        )

        self.pin_tree.column(
            "Min",
            width=80,
            anchor="center",
        )

        self.pin_tree.column(
            "Max",
            width=80,
            anchor="center",
        )

        self.pin_tree.pack(
            expand=True,
            fill="both",
            padx=10,
            pady=10,
        )

        return self.tab_pins

    # =====================================================
    # TIMER
    # =====================================================

    def updateTimer(self, timestamp_ms):
        minutes = timestamp_ms // 60000
        seconds = (timestamp_ms % 60000) // 1000
        milliseconds = timestamp_ms % 1000

        self.timer_label.config(text=(f"{minutes:02}:{seconds:02}:{milliseconds:03}"))

    # =====================================================
    # REGISTER TYPE
    # =====================================================

    def getRegisterTypeName(self, register_type):
        return self.register_type_names.get(
            register_type,
            f"Unknown (0x{register_type:02X})",
        )

    # =====================================================
    # UPDATE PIN
    # =====================================================

    def updatePinTree(
        self,
        pinID,
        value,
        register_type,
        is_input,
        min_value,
        max_value,
    ):
        # ---------------------------------------------
        # Your current convention:
        #
        # is_input = True
        #     -> writable
        #     -> Read Only = No
        #
        # is_input = False
        #     -> read-only
        #     -> Read Only = Yes
        # ---------------------------------------------

        read_only = "No" if is_input else "Yes"

        register_type_name = self.getRegisterTypeName(register_type)

        values = (
            pinID,
            value,
            register_type_name,
            read_only,
            min_value,
            max_value,
        )

        # ---------------------------------------------
        # Existing pin
        # ---------------------------------------------

        if pinID in self.pin_values:
            item_id = self.pin_values[pinID]["item"]

            self.pin_tree.item(
                item_id,
                values=values,
            )

            return

        # ---------------------------------------------
        # New pin
        # ---------------------------------------------

        item_id = self.pin_tree.insert(
            "",
            tk.END,
            values=values,
        )

        self.pin_values[pinID] = {
            "item": item_id,
        }

