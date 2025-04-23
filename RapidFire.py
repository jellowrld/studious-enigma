import pymem
import pymem.process
import tkinter as tk
from tkinter import messagebox
import itertools

# Game executable name
PROCESS_NAME = "M1-Win64-Shipping.exe"

# Signature and mask
RapidFireSig = b"\x72\x00\xF3\x0F\x10\x87\x00\x00\x00\x00\x48\x8B\xCF"
RapidFireMask = "x?xxxx????xxx"

# Patch bytes
original_byte = b"\x72"
patched_byte = b"\x77"

# Global vars
pm = None
rapid_fire_ptr = None

# Rainbow colors
rainbow_colors = itertools.cycle(["red", "orange", "yellow", "green", "cyan", "blue", "magenta"])

def aob_scan(pm, base, size, pattern, mask):
    bytes_read = pm.read_bytes(base, size)
    pattern_len = len(mask)

    for i in range(size - pattern_len):
        match = True
        for j in range(pattern_len):
            if mask[j] == 'x' and bytes_read[i + j] != pattern[j]:
                match = False
                break
        if match:
            return base + i
    return None

def attach_and_scan():
    global pm, rapid_fire_ptr

    try:
        pm = pymem.Pymem(PROCESS_NAME)
        module = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME)
        base = module.lpBaseOfDll
        size = module.SizeOfImage

        rapid_fire_ptr = aob_scan(pm, base, size, RapidFireSig, RapidFireMask)
        if not rapid_fire_ptr:
            raise RuntimeError("Unable to find RapidFire pattern")

        pointer_label.config(text=f"Pointer: 0x{rapid_fire_ptr:X}")
        update_status()

        toggle_button.config(text="Attached", state="disabled")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_status():
    if not pm or not rapid_fire_ptr:
        status_label.config(text="Status: Not attached", fg="gray")
        return

    current = pm.read_bytes(rapid_fire_ptr, 1)
    if current == patched_byte:
        status_label.config(text="Status: ON", fg="green")
        second_toggle_button.config(text="Turn OFF")
    elif current == original_byte:
        status_label.config(text="Status: OFF", fg="red")
        second_toggle_button.config(text="Turn ON")
    else:
        status_label.config(text=f"Unknown Byte: {current.hex()}", fg="orange")

def toggle_patch():
    if not pm or not rapid_fire_ptr:
        messagebox.showwarning("Warning", "Not attached to process.")
        return

    current = pm.read_bytes(rapid_fire_ptr, 1)
    if current == original_byte:
        pm.write_bytes(rapid_fire_ptr, patched_byte, 1)
    elif current == patched_byte:
        pm.write_bytes(rapid_fire_ptr, original_byte, 1)
    update_status()

def cycle_colors():
    title_color = next(rainbow_colors)
    pointer_label.config(fg=title_color)
    status_label.config(fg=title_color)
    title_label.config(fg=title_color)
    root.after(100, cycle_colors)

def bind_keypress(event):
    toggle_patch()

def enforce_topmost():
    root.attributes("-topmost", True)
    root.wm_attributes("-topmost", True)
    root.after(1000, enforce_topmost)

# GUI setup
root = tk.Tk()
root.title("RapidFire by Jell")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.wm_attributes("-topmost", True)
root.config(bg='black')
root.attributes("-transparentcolor", "black")

# Position in top-right corner
screen_width = root.winfo_screenwidth()
root.geometry(f"300x200+{screen_width - 310}+10")

# Title label with rainbow color animation
title_label = tk.Label(root, text="RapidFire by Jell", font=("Segoe UI", 12, "bold"), fg="white", bg="black")
title_label.pack(pady=(5, 0))

pointer_label = tk.Label(root, text="Pointer: N/A", font=("Segoe UI", 10), bg='black')
pointer_label.pack(pady=(10, 0))

status_label = tk.Label(root, text="Status: Not attached", font=("Segoe UI", 12), bg='black')
status_label.pack(pady=(5, 0))

toggle_button = tk.Button(root, text="Attach and Scan", command=attach_and_scan, font=("Segoe UI", 11), bg='gray20', fg='white', activebackground='gray30')
toggle_button.pack(pady=10)

second_toggle_button = tk.Button(root, text="Toggle", command=toggle_patch, font=("Segoe UI", 11), bg='gray20', fg='white', activebackground='gray30')
second_toggle_button.pack(pady=(5, 10))

root.bind("`", bind_keypress)

cycle_colors()
enforce_topmost()
root.mainloop()