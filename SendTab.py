import tkinter as tk
from tkinter import ttk, scrolledtext


class SendTab:
    def __init__(self, notebook, send_callback=None):
        self.notebook = notebook
        self.send_callback = send_callback

        self.tab_Send = ttk.Frame(self.notebook)

        # ================= HEADER =================

        self.header_frame = ttk.Frame(self.tab_Send)

        self.timer_label_title = ttk.Label(self.header_frame, text="Time:")

        self.timer_label = ttk.Label(
            self.header_frame,
            text="00:00:000",
            font=("Arial", 12, "bold"),
        )

        # ================= PIN DATA =================

        # pinID -> {
        #     type,
        #     is_input,
        #     min,
        #     max
        # }
        self.pins = {}

        self.selected_pin = tk.StringVar()
        self.value_var = tk.StringVar()

        # ================= UI =================

        self.controls_frame = ttk.Frame(self.tab_Send)

        # ================= PIN =================

        self.pin_label = ttk.Label(self.controls_frame, text="Pin:")

        self.pin_combo = ttk.Combobox(
            self.controls_frame,
            textvariable=self.selected_pin,
            state="readonly",
            width=15,
        )

        self.pin_combo.bind(
            "<<ComboboxSelected>>",
            self.on_pin_selected,
        )

        # ================= VALUE =================

        self.value_label = ttk.Label(self.controls_frame, text="Value:")

        self.value_entry = ttk.Entry(
            self.controls_frame,
            textvariable=self.value_var,
            width=15,
        )

        # ================= SEND =================

        self.send_button = ttk.Button(
            self.controls_frame,
            text="Send",
            command=self.send_packet,
        )

        # ================= LOG =================

        self.log = scrolledtext.ScrolledText(
            self.tab_Send,
            width=80,
            height=15,
            font=("Courier", 10),
        )

    # =================================================
    # DISPLAY
    # =================================================

    def Display(self):
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

        self.controls_frame.pack(
            fill="x",
            padx=10,
            pady=5,
        )

        self.pin_label.pack(
            side="left",
            padx=(0, 5),
        )

        self.pin_combo.pack(
            side="left",
            padx=5,
        )

        self.value_label.pack(
            side="left",
            padx=(15, 5),
        )

        self.value_entry.pack(
            side="left",
            padx=5,
        )

        self.send_button.pack(
            side="left",
            padx=5,
        )

        self.log.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        # Initially there is no pin selected.
        self.value_entry.config(state="disabled")
        self.send_button.config(state="disabled")

        return self.tab_Send

    # =================================================
    # UPDATE PINS
    # =================================================

    def updatePins(
        self,
        pinID,
        register_type,
        is_input,
        min_value,
        max_value,
    ):
        self.pins[pinID] = {
            "type": register_type,
            "is_input": is_input,
            "min": min_value,
            "max": max_value,
        }

        # Only pins marked as input are writable
        writable_pins = [
            pin_id for pin_id, data in self.pins.items() if data["is_input"]
        ]

        writable_pins.sort()

        self.pin_combo["values"] = writable_pins

        # If currently selected pin became unavailable
        current = self.selected_pin.get()

        if current:
            try:
                current_id = int(current)
            except ValueError:
                current_id = None

            if current_id not in writable_pins:
                self.selected_pin.set("")
                self.value_var.set("")

                self.value_entry.config(state="disabled")

                self.send_button.config(state="disabled")

    # =================================================
    # PIN SELECTED
    # =================================================

    def on_pin_selected(self, event=None):
        pin = self.selected_pin.get()

        if not pin:
            self.value_entry.config(state="disabled")

            self.send_button.config(state="disabled")

            return

        try:
            pin_id = int(pin)
        except ValueError:
            self.value_entry.config(state="disabled")

            self.send_button.config(state="disabled")

            return

        pin_data = self.pins.get(pin_id)

        if not pin_data:
            self.value_entry.config(state="disabled")

            self.send_button.config(state="disabled")

            return

        # is_input == True means writable
        if pin_data["is_input"]:
            self.value_entry.config(state="normal")

            self.send_button.config(state="normal")

        else:
            self.value_entry.config(state="disabled")

            self.send_button.config(state="disabled")

    # =================================================
    # SEND
    # =================================================

    def send_packet(self):
        pin = self.selected_pin.get()
        value_text = self.value_var.get()

        if not pin:
            self.log.insert(
                tk.END,
                "❌ Select a writable pin\n",
            )
            return

        if not value_text:
            self.log.insert(
                tk.END,
                "❌ Enter a value\n",
            )
            return

        try:
            pin_id = int(pin)
        except ValueError:
            self.log.insert(
                tk.END,
                "❌ Invalid pin\n",
            )
            return

        pin_data = self.pins.get(pin_id)

        if not pin_data:
            self.log.insert(
                tk.END,
                "❌ Invalid pin\n",
            )
            return

        # =================================================
        # Writable check
        #
        # true  -> writable
        # false -> read-only
        # =================================================

        if not pin_data["is_input"]:
            self.log.insert(
                tk.END,
                f"❌ Pin {pin_id} is read-only\n",
            )
            return

        # =================================================
        # Value
        # =================================================

        try:
            value = int(value_text)
        except ValueError:
            self.log.insert(
                tk.END,
                "❌ Value must be an integer\n",
            )
            return

        # =================================================
        # Range
        # =================================================

        min_value = pin_data["min"]
        max_value = pin_data["max"]

        if not (min_value <= value <= max_value):
            self.log.insert(
                tk.END,
                f"❌ Value must be between {min_value} and {max_value}\n",
            )
            return

        # =================================================
        # Send
        # =================================================

        if self.send_callback:
            try:
                self.send_callback(
                    pin_id,
                    value,
                )

            except Exception as exc:
                self.log.insert(
                    tk.END,
                    f"❌ Send error: {exc}\n",
                )
                return

        self.log.insert(
            tk.END,
            f"✔ Sent Pin {pin_id} = {value}\n",
        )

        self.log.see(tk.END)

    # =================================================
    # TIMER
    # =================================================

    def updateTimer(self, timestamp_ms):
        minutes = timestamp_ms // 60000
        seconds = (timestamp_ms % 60000) // 1000
        milliseconds = timestamp_ms % 1000

        self.timer_label.config(text=(f"{minutes:02}:{seconds:02}:{milliseconds:03}"))

