import serial
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

from MonitorTab import MonitorTab

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200 

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"Cannot open {PORT}: {e}")
    exit(1)

# ===== واجهة المستخدم =====
root = tk.Tk()
root.title("Fake Drivers Monitor")
root.geometry("1000x600")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# --- Monitor Tab ---
# def monitorTab (notebook) :
#     tab_monitor = ttk.Frame(notebook)
#     text_area = scrolledtext.ScrolledText(
#     tab_monitor,
#     width=80,
#     height=20,
#     state='disabled',
#     font=("Courier", 10))
#     text_area.pack(padx=10, pady=10, expand=True, fill='both')
#     return tab_monitor


tabMonitor = MonitorTab(notebook)
notebook.add(tabMonitor.Display(), text="Monitor")



# --- Registers Tab ---
tab_registers = ttk.Frame(notebook)
notebook.add(tab_registers, text="Registers")

columns = ("Time", "PinID", "Value", "Type", "IsInput", "Min", "Max")
tree = ttk.Treeview(tab_registers, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100, anchor='center')
tree.pack(expand=True, fill='both', padx=10, pady=10)

# --- Pins Tab ---
tab_pins = ttk.Frame(notebook)
notebook.add(tab_pins, text="Pin Values")

pin_columns = ("PinID", "Value")
pin_tree = ttk.Treeview(tab_pins, columns=pin_columns, show="headings")
for col in pin_columns:
    pin_tree.heading(col, text=col)
    pin_tree.column(col, width=100, anchor='center')
pin_tree.pack(expand=True, fill='both', padx=10, pady=10)

# لتخزين آخر قيمة لكل pin
pin_values = {}  # {pinID: value}

# تحديث أو إدراج قيمة Pin
def update_pin_tree(pinID, value):
    if pinID in pin_values:
        # تحديث السطر الموجود
        item_id = pin_values[pinID]['item']
        pin_tree.set(item_id, "Value", value)
    else:
        # إدراج جديد
        item_id = pin_tree.insert("", tk.END, values=(pinID, value))
        pin_values[pinID] = {'value': value, 'item': item_id}
    pin_values[pinID]['value'] = value

# --- Send Tab ---
tab_send = ttk.Frame(notebook)
notebook.add(tab_send, text="Send")

entry_text = tk.Entry(tab_send)
entry_text.pack(padx=10, pady=10, side='left', expand=True, fill='x')

def send_text():
    data = entry_text.get().strip()
    if not data:
        return
    try:
        ser.write((data + "\n").encode())
        entry_text.delete(0, tk.END)
    except serial.SerialException as e:
        messagebox.showerror("Serial Error", str(e))

tk.Button(tab_send, text="Send", command=send_text).pack(padx=10, pady=10, side='left')

# --- Close ---
def close_program():
    try:
        ser.close()
    except:
        pass
    root.destroy()

tk.Button(root, text="Close", command=close_program).pack(pady=5)

# ===== عرض البيانات في Monitor =====
def update_text_area(text):
    text_area.configure(state='normal')
    text_area.insert(tk.END, text + "\n")
    text_area.see(tk.END)
    text_area.configure(state='disabled')

# ===== Serial Parser =====
buffer = bytearray()

def parse_register_packet(packet):
    if len(packet) < 7:
        return
    if packet[1] != 0x01:
        return
    length = packet[2]
    timestamp = packet[3] | (packet[4]<<8) | (packet[5]<<16) | (packet[6]<<24)
    regs = []
    idx = 7
    for _ in range(length):
        if idx + 9 > len(packet):
            break
        pinID = packet[idx]
        value = packet[idx+1] | (packet[idx+2]<<8)
        isInput = bool(packet[idx+3])
        reg_type = packet[idx+4]
        minValue = packet[idx+5] | (packet[idx+6]<<8)
        maxValue = packet[idx+7] | (packet[idx+8]<<8)
        regs.append((timestamp, pinID, value, reg_type, isInput, minValue, maxValue))
        idx += 9
    return regs

def read_serial():
    global buffer
    while True:
        try:
            if ser.in_waiting:
                buffer += ser.read(ser.in_waiting)

                while True:
                    if len(buffer) < 2:
                        break
                    if buffer[0] != 0xAA:
                        buffer.pop(0)
                        continue
                    if 0x55 not in buffer:
                        break
                    end_index = buffer.index(0x55)
                    packet = buffer[:end_index + 1]
                    buffer = buffer[end_index + 1:]

                    # HEX Monitor
                    hex_str = ' '.join(f"{b:02X}" for b in packet)
                    root.after(0, lambda s=hex_str: update_text_area(s))

                    # Registers Tab
                    regs = parse_register_packet(packet)
                    if regs:
                        for r in regs:
                            root.after(0, lambda row=r: tree.insert("", tk.END, values=row))
                            # Pins Tab
                            timestamp, pinID, value, reg_type, isInput, minV, maxV = r
                            root.after(0, lambda pid=pinID, val=value: update_pin_tree(pid, val))

        except serial.SerialException:
            break

# ===== تشغيل Thread =====
thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

root.mainloop()