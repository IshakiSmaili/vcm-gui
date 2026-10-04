# 🖥️ VCM GUI — Firmware Testing Tool

## Overview

**VCM GUI** is a lightweight graphical tool created specifically for **testing and debugging VCM firmware**.

It provides a simple interface for connecting to a microcontroller, monitoring communication, inspecting register data, and sending test values to the firmware.

This GUI is **not the final VCM application**. It is a development and testing tool used during the implementation of the VCM firmware and communication protocol.

## Purpose

The main purpose of this project is to make firmware development and debugging easier by providing a visual interface for testing the VCM communication layer.

It can be used to:

* Connect to the microcontroller.
* Monitor packets exchanged between the PC and MCU.
* Inspect register values.
* Send register updates to the firmware.
* Debug communication and firmware behavior.

## Relationship with VCM

VCM is designed to allow virtual components on a computer to interact with real microcontroller firmware.

The current architecture is divided into separate parts:

```text
┌──────────────┐
│   VCM GUI    │
│  Test Tool   │
└──────┬───────┘
       │
       │ Communication Protocol
       │
┌──────▼───────┐
│ VCM Firmware │
│     MCU      │
└──────────────┘
```

The **VCM Firmware** runs on the microcontroller, while **VCM GUI** acts as a temporary development tool for testing the firmware and protocol.

The GUI may eventually be replaced or superseded by a more complete VCM application.

## Features

* Serial communication with the MCU.
* Packet monitoring.
* Register inspection.
* Register value updates.
* Protocol testing.
* Basic debugging tools.
* Simple interface for firmware development.

## Technology

* Python
* Python Virtual Environment (`venv`)
* Serial communication
* GUI toolkit
* VCM communication protocol

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### Linux / Bash

```bash
source .venv/bin/activate
```

### Fish

```fish
source .venv/bin/activate.fish
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running

With the virtual environment activated:

```bash
python vcm_gui.py
```

## Project Status

This project is currently a **development and testing tool**.

The interface and functionality may change frequently as the VCM firmware and communication protocol evolve.

It should not be considered the final user-facing VCM application.

## Related Projects

* **VCM Firmware** — Firmware running on the microcontroller.
* **VCM** — The broader Virtual Components for Microcontrollers project.

---

> **Note:** VCM GUI exists primarily to test and debug the firmware during development. It is intentionally kept simple and should not be confused with the future production VCM application.
