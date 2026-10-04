import threading
import tkinter as tk
from tkinter import messagebox, ttk

import serial
from serial import SerialException

from MonitorTab import MonitorTab
from PinsTab import PinsTab
from SendTab import SendTab


# =========================================================
# Serial configuration
# =========================================================

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
SERIAL_TIMEOUT = 0.1

START_BYTE = 0xAA
END_BYTE = 0x55

MSG_TYPE_REG_BATCH = 0x01
MSG_TYPE_ACK = 0x02
MSG_TYPE_NAK = 0x03
MSG_TYPE_REG_UPDATE = 0x04

DIGITAL_INPUT = 0x01
DIGITAL_OUTPUT = 0x02
ANALOG_INPUT = 0x03
ANALOG_OUTPUT = 0x04
PWM_OUTPUT = 0x05
SPECIAL_FUNCTION = 0x06

REGISTER_TYPE_NAMES = {
    DIGITAL_INPUT: "Digital Input",
    DIGITAL_OUTPUT: "Digital Output",
    ANALOG_INPUT: "Analog Input",
    ANALOG_OUTPUT: "Analog Output",
    PWM_OUTPUT: "PWM Output",
    SPECIAL_FUNCTION: "Special Function",
}

# REG_BATCH:
# AA | type | count | timestamp[4] | registers[count * 9] | CRC | 55
REG_BATCH_HEADER_SIZE = 7
REGISTER_SIZE = 8

# REG_UPDATE:
# AA | type | count | entries[count * 3] | CRC | 55
REG_UPDATE_HEADER_SIZE = 3
REG_UPDATE_ENTRY_SIZE = 3

# ACK / NAK:
# AA | type | timestamp[4] | CRC | 55
ACK_PACKET_SIZE = 8


# =========================================================
# Serial connection
# =========================================================

try:
    ser = serial.Serial(
        PORT,
        BAUDRATE,
        timeout=SERIAL_TIMEOUT,
    )
except (SerialException, OSError) as exc:
    error_root = tk.Tk()
    error_root.withdraw()

    messagebox.showerror(
        "Serial Error",
        f"Cannot open {PORT}:\n{exc}",
        parent=error_root,
    )

    error_root.destroy()
    raise SystemExit(1)


# =========================================================
# UI
# =========================================================

root = tk.Tk()
root.title("VCM Monitor")
root.geometry("1000x600")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

tab_monitor = MonitorTab(notebook)
notebook.add(tab_monitor.Display(), text="Monitor")

tab_pins = PinsTab(notebook)
notebook.add(tab_pins.Display(), text="Pin Values")


# =========================================================
# CRC and packet helpers
# =========================================================


def calculate_crc(data):
    crc = 0

    for byte in data:
        crc ^= byte

    return crc & 0xFF


def is_valid_packet(packet):
    if len(packet) < 5:
        return False

    if packet[0] != START_BYTE or packet[-1] != END_BYTE:
        return False

    return packet[-2] == calculate_crc(packet[1:-2])


def read_u16_le(data, index):
    return data[index] | (data[index + 1] << 8)


def read_u32_le(data, index):
    return (
        data[index]
        | (data[index + 1] << 8)
        | (data[index + 2] << 16)
        | (data[index + 3] << 24)
    )


def build_reg_update_packet(pin_id, value):
    pin_id = int(pin_id)
    value = int(value)

    if not 0 <= pin_id <= 0xFF:
        raise ValueError("Pin ID must be between 0 and 255.")

    if not 0 <= value <= 0xFFFF:
        raise ValueError("Value must be between 0 and 65535.")

    packet = bytearray(
        [
            START_BYTE,
            MSG_TYPE_REG_UPDATE,
            1,
            pin_id,
            value & 0xFF,
            (value >> 8) & 0xFF,
        ]
    )

    packet.append(calculate_crc(packet[1:]))
    packet.append(END_BYTE)

    return bytes(packet)


# =========================================================
# Parse REG_BATCH
# =========================================================


def parse_reg_batch_packet(packet):
    if not is_valid_packet(packet):
        return None

    if len(packet) < REG_BATCH_HEADER_SIZE + 2:
        return None

    if packet[1] != MSG_TYPE_REG_BATCH:
        return None

    count = packet[2]

    expected_size = REG_BATCH_HEADER_SIZE + count * REGISTER_SIZE + 2

    if len(packet) != expected_size:
        return None

    timestamp = read_u32_le(packet, 3)
    registers = []

    index = REG_BATCH_HEADER_SIZE

    for _ in range(count):
        pin_id = packet[index]

        value = read_u16_le(packet, index + 1)

        # Temporary until writability is implemented properly.
        is_input = True

        register_type = packet[index + 3]

        min_value = read_u16_le(packet, index + 4)

        max_value = read_u16_le(packet, index + 6)

        registers.append(
            {
                "timestamp": timestamp,
                "pin_id": pin_id,
                "value": value,
                "type": register_type,
                "is_input": is_input,
                "min_value": min_value,
                "max_value": max_value,
            }
        )

        index += REGISTER_SIZE

    return {
        "timestamp": timestamp,
        "registers": registers,
    }


# =========================================================
# Parse ACK / NAK
# =========================================================


def parse_ack_nak_packet(packet):
    if not is_valid_packet(packet) or len(packet) != ACK_PACKET_SIZE:
        return None

    msg_type = packet[1]

    if msg_type not in (MSG_TYPE_ACK, MSG_TYPE_NAK):
        return None

    return {
        "type": "ACK" if msg_type == MSG_TYPE_ACK else "NAK",
        "timestamp": read_u32_le(packet, 2),
    }


# =========================================================
# Packet framing
# =========================================================


def get_expected_packet_size(data):
    if len(data) < 2 or data[0] != START_BYTE:
        return None

    msg_type = data[1]

    if msg_type == MSG_TYPE_REG_BATCH:
        if len(data) < 3:
            return None

        return REG_BATCH_HEADER_SIZE + data[2] * REGISTER_SIZE + 2

    if msg_type == MSG_TYPE_REG_UPDATE:
        if len(data) < 3:
            return None

        return REG_UPDATE_HEADER_SIZE + data[2] * REG_UPDATE_ENTRY_SIZE + 2

    if msg_type in (MSG_TYPE_ACK, MSG_TYPE_NAK):
        return ACK_PACKET_SIZE

    return None


# =========================================================
# UI-safe logging
# =========================================================


def log_message(message):
    root.after(0, lambda msg=message: tab_monitor.updateTextArea(msg))


def update_register_ui(register):
    tab_pins.updatePinTree(
        register["pin_id"],
        register["value"],
        register["type"],
        register["is_input"],
        register["min_value"],
        register["max_value"],
    )

    tab_send.updatePins(
        pinID=register["pin_id"],
        register_type=register["type"],
        is_input=register["is_input"],
        min_value=register["min_value"],
        max_value=register["max_value"],
    )


# =========================================================
# Send tab
# =========================================================


def send_callback(pin_id, value):
    try:
        packet = build_reg_update_packet(pin_id, value)

        with serial_lock:
            if not ser.is_open:
                raise SerialException("Serial port is closed.")

            ser.write(packet)
            ser.flush()

        log_message(f"TX: {packet.hex(' ').upper()}")

    except (ValueError, SerialException, OSError) as exc:
        log_message(f"Send error: {exc}")


serial_lock = threading.Lock()

tab_send = SendTab(notebook, send_callback)
notebook.add(tab_send.Display(), text="Send Value")


# =========================================================
# Stream parser
# =========================================================

rx_buffer = bytearray()
stop_event = threading.Event()


def process_packet(packet):
    hex_string = packet.hex(" ").upper()
    log_message(f"RX: {hex_string}")

    if not is_valid_packet(packet):
        log_message("Invalid packet CRC or END byte.")
        return

    msg_type = packet[1]

    if msg_type == MSG_TYPE_REG_BATCH:
        batch = parse_reg_batch_packet(packet)

        if batch is None:
            log_message("Invalid REG_BATCH structure.")
            return

        for register in batch["registers"]:
            root.after(
                0,
                lambda item=register: update_register_ui(item),
            )

        root.after(
            0,
            lambda ts=batch["timestamp"]: tab_pins.updateTimer(ts),
        )

    elif msg_type in (MSG_TYPE_ACK, MSG_TYPE_NAK):
        response = parse_ack_nak_packet(packet)

        if response is not None:
            log_message(f"{response['type']} received at {response['timestamp']}")

    elif msg_type == MSG_TYPE_REG_UPDATE:
        # Normally the PC sends REG_UPDATE to the MCU.
        log_message("Received REG_UPDATE from MCU.")

    else:
        log_message(f"Unknown message type: 0x{msg_type:02X}")


def process_buffer():
    while True:
        try:
            start_index = rx_buffer.index(START_BYTE)
        except ValueError:
            rx_buffer.clear()
            return

        if start_index:
            del rx_buffer[:start_index]

        if len(rx_buffer) < 2:
            return

        expected_size = get_expected_packet_size(rx_buffer)

        if expected_size is None:
            # Drop only the start byte, then search for the next frame.
            del rx_buffer[0]
            continue

        if len(rx_buffer) < expected_size:
            return

        # Recover from a bad frame without discarding a following frame.
        if rx_buffer[expected_size - 1] != END_BYTE:
            del rx_buffer[0]
            continue

        packet = bytes(rx_buffer[:expected_size])
        del rx_buffer[:expected_size]

        process_packet(packet)


# =========================================================
# Serial reader thread
# =========================================================


def read_serial():
    while not stop_event.is_set():
        try:
            with serial_lock:
                if not ser.is_open:
                    break

                waiting = ser.in_waiting
                data = ser.read(waiting if waiting else 1)

            if not data:
                continue

            rx_buffer.extend(data)
            process_buffer()

        except (SerialException, OSError) as exc:
            if not stop_event.is_set():
                log_message(f"Serial read error: {exc}")
            break


# =========================================================
# Close application
# =========================================================


def close_program():
    stop_event.set()

    try:
        if ser.is_open:
            ser.close()
    except (SerialException, OSError):
        pass

    root.destroy()


ttk.Button(
    root,
    text="Close",
    command=close_program,
).pack(pady=5)

threading.Thread(target=read_serial, daemon=True).start()

root.protocol("WM_DELETE_WINDOW", close_program)
root.mainloop()
