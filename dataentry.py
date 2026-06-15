#dataentry.py
#user input screen for bcalc external ballistics calculator

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Tuple
from tkinter import messagebox
import os

try:
    from dataholder import load_cartridge_data
except ImportError:
    print("Warning: dataholder.py not found. Using mock data.")
    load_cartridge_data = None

import dataholder2

from config import COLORS, FONTS, INPUT_PARAMS, VALIDATION_RULES


def setup_styles(style):
    """Define all custom styles."""
    style.configure("TEntry", font=(FONTS['family'], FONTS['label_size']))
    style.configure("TCombobox", font=(FONTS['family'], FONTS['label_size']))
    style.configure("CustomFrame.TFrame", background=COLORS['bg_frame'])
    style.configure("CustomLabel.TLabel", foreground=COLORS['label'], background=COLORS['bg_frame'], font=(FONTS['family'], FONTS['label_size']))
    style.configure("Unit.TLabel", foreground=COLORS['unit'], background=COLORS['bg_frame'], font=(FONTS['family'], FONTS['unit_size']))
    style.configure("Title.TLabel", foreground=COLORS['error_text'], background=COLORS['bg_frame'], font=(FONTS['family'], FONTS['title_size'], "bold"))
    style.configure("TButton", font=(FONTS['family'], FONTS['label_size']))
    style.configure("White.TCombobox", fieldbackground=COLORS['white'], foreground="black", font=(FONTS['family'], FONTS['label_size']))
    style.configure("White.TEntry", fieldbackground=COLORS['white'], foreground="black", font=(FONTS['family'], FONTS['label_size']))
    style.configure("Gray.TEntry", fieldbackground=COLORS['gray'], foreground="black", font=(FONTS['family'], FONTS['label_size']))
    style.configure("Error.TEntry", fieldbackground=COLORS['error_bg'], foreground="black", font=(FONTS['family'], FONTS['unit_size']))


def create_row(parent, label_text, row, style_name="White.TEntry", default_val="", unit=""):
    """Create a labeled input row with entry, unit label, and error label."""
    lbl = ttk.Label(parent, text=label_text, style="CustomLabel.TLabel")
    lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)

    row_frame = ttk.Frame(parent, style="CustomFrame.TFrame")
    row_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)

    entry = ttk.Entry(row_frame, width=12, style=style_name, justify='center')
    entry.config(font=(FONTS['family'], FONTS['label_size']))
    entry.pack(side="left")
    entry.insert(0, default_val)

    if unit:
        unit_lbl = ttk.Label(row_frame, text=unit, style="Unit.TLabel")
        unit_lbl.pack(side="left", padx=(5, 0))

    error_lbl = ttk.Label(row_frame, text="", foreground=COLORS['error_text'], background=COLORS['bg_frame'], font=(FONTS['family'], FONTS['unit_size']))
    error_lbl.pack(side="left", padx=(5, 0))

    return entry, error_lbl


def validate_field(key, entry, error_lbl):
    """Validate a single field on FocusOut and update UI accordingly."""
    value_str = entry.get().strip()

    if not value_str:
        entry.config(style="White.TEntry")
        error_lbl.config(text="")
        return

    try:
        val = float(value_str)
    except ValueError:
        entry.config(style="Error.TEntry")
        error_lbl.config(text="Must be a number")
        return

    if key in VALIDATION_RULES:
        min_val, max_val = VALIDATION_RULES[key]
        if not (min_val <= val <= max_val):
            entry.config(style="Error.TEntry")
            error_lbl.config(text=f"Range: [{min_val} to {max_val}]")
            return

    entry.config(style="White.TEntry")
    error_lbl.config(text="")


def calculate_ballistic_values(fields):
    """Calculate cross-sectional area and sectional density."""
    try:
        caliber = float(fields["caliber"].get())
        weight = float(fields["weight"].get())

        crs_sec_area = ((caliber / 2) ** 2) * 3.1415927

        if caliber != 0:
            sec_den = (weight / 7000) / (caliber ** 2)
        else:
            sec_den = 0.0

        fields["crs_sec_area"].config(state="normal")
        fields["crs_sec_area"].delete(0, tk.END)
        fields["crs_sec_area"].insert(0, f"{crs_sec_area:.4f}")
        fields["crs_sec_area"].config(state="readonly")

        fields["sec_den"].config(state="normal")
        fields["sec_den"].delete(0, tk.END)
        fields["sec_den"].insert(0, f"{sec_den:.4f}")
        fields["sec_den"].config(state="readonly")

    except (ValueError, ZeroDivisionError):
        fields["crs_sec_area"].config(state="normal")
        fields["crs_sec_area"].delete(0, tk.END)
        fields["crs_sec_area"].insert(0, "0.0000")
        fields["crs_sec_area"].config(state="readonly")

        fields["sec_den"].config(state="normal")
        fields["sec_den"].delete(0, tk.END)
        fields["sec_den"].insert(0, "0.0000")
        fields["sec_den"].config(state="readonly")


def validate_all(fields, error_labels):
    """Validate all fields and return (is_valid, error_list)."""
    errors = []
    for key, entry in fields.items():
        # Skip calculated fields
        if key in ["caliber", "crs_sec_area", "sec_den"]:
            continue

        value_str = entry.get().strip()
        if not value_str:
            errors.append(f"{key}: Empty value")
            entry.config(style="Error.TEntry")
            error_labels[key].config(text="Required")
            continue

        try:
            val = float(value_str)
        except ValueError:
            errors.append(f"{key}: Not a number")
            entry.config(style="Error.TEntry")
            error_labels[key].config(text="Must be a number")
            continue

        if key in VALIDATION_RULES:
            min_val, max_val = VALIDATION_RULES[key]
            if not (min_val <= val <= max_val):
                errors.append(f"{key}: out of range [{min_val} to {max_val}]")
                entry.config(style="Error.TEntry")
                error_labels[key].config(text=f"Range: [{min_val} to {max_val}]")
                continue

        entry.config(style="White.TEntry")
        error_labels[key].config(text="")

    return len(errors) == 0, errors

def main():
    # 1. Load Cartridge Data
    cartridge_data = {}
    if load_cartridge_data:
        try:
            cartridge_data = load_cartridge_data("datacartcal.csv")
            if not cartridge_data:
                print("Warning: No data found in datacartcal.csv")
        except Exception as e:
            print(f"Error loading cartridge data: {e}")
            cartridge_data = {
                ".308 Win": {"caliber": 0.308, "g1": 0.450, "g7": 0.230, "weight": 143},
                ".30-06 Sprg": {"caliber": 0.308, "g1": 0.420, "g7": 0.210, "weight": 150},
                "6.5 Creedmoor": {"caliber": 0.264, "g1": 0.395, "g7": 0.210, "weight": 140},
                ".223 Rem": {"caliber": 0.224, "g1": 0.250, "g7": 0.130, "weight": 55},
                "7mm Rem Mag": {"caliber": 0.284, "g1": 0.500, "g7": 0.260, "weight": 160},
                ".338 Lapua": {"caliber": 0.338, "g1": 0.650, "g7": 0.340, "weight": 250},
            }
    else:
        cartridge_data = {
            ".308 Win": {"caliber": 0.308, "g1": 0.450, "g7": 0.230, "weight": 143},
            ".30-06 Sprg": {"caliber": 0.308, "g1": 0.420, "g7": 0.210, "weight": 150},
            "6.5 Creedmoor": {"caliber": 0.264, "g1": 0.395, "g7": 0.210, "weight": 140},
            ".223 Rem": {"caliber": 0.224, "g1": 0.250, "g7": 0.130, "weight": 55},
            "7mm Rem Mag": {"caliber": 0.284, "g1": 0.500, "g7": 0.260, "weight": 160},
            ".338 Lapua": {"caliber": 0.338, "g1": 0.650, "g7": 0.340, "weight": 250},
        }

    dataholder2.clear_runs()

    # 2. Create Root Window
    root = ttk.Tk()
    root.title("Bcalc External Ballistics")
    root.geometry("650x850")

    # 3. Initialize Styles
    style = ttk.Style()
    style.theme_use("litera")
    setup_styles(style)

    # 4. Main Container Frame
    main_frame = ttk.Frame(root, padding=20, style="CustomFrame.TFrame")
    main_frame.pack(fill=BOTH, expand=True)

    # Configure 3 columns:
    # Col 0: Labels (fixed width)
    # Col 1: Entries (expandable)
    # Col 2: Image (fixed width, spans rows)
    main_frame.columnconfigure(0, weight=0)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=0)

    # Title Header
    title_label = ttk.Label(main_frame, text="Enter Data for up to 3 Rounds", style="Title.TLabel")
    title_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

    # Variables
    cartridge_var = tk.StringVar()
    drag_function_var = tk.StringVar()
    fields: Dict[str, ttk.Entry] = {}
    error_labels: Dict[str, ttk.Label] = {}
    store_count = [0]

    # 5. Cartridge Dropdown (Row 1, Spans Col 0-1)
    ttk.Label(main_frame, text="Cartridge", style="CustomLabel.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    combo_cartridge = ttk.Combobox(
        main_frame,
        textvariable=cartridge_var,
        values=list(cartridge_data.keys()),
        state="readonly",
        width=55,
        justify='center',
        style="White.TCombobox",
    )
    combo_cartridge.config(font=(FONTS['family'], FONTS['label_size']))
    combo_cartridge.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
    if cartridge_data:
        combo_cartridge.current(0)

    # 5b. Image Frame (Row 2, Col 2, spans all remaining rows)
    image_frame = ttk.Frame(main_frame, style="CustomFrame.TFrame")
    image_frame.grid(row=2, column=2, rowspan=25, sticky="ns", padx=5, pady=5)

    # Load Image
    try:
        from PIL import Image, ImageTk
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bcalcexticon.png")
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img.thumbnail((180, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            img_label = ttk.Label(image_frame, image=photo, background="white")
            img_label.image = photo  # Keep reference!
            img_label.pack(pady=10)
        else:
            ttk.Label(image_frame, text="[Image not found]", style="Unit.TLabel").pack()
    except ImportError:
        # Fallback if Pillow not installed
        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bcalcexticon.png")
            photo = tk.PhotoImage(file=img_path)
            img_label = ttk.Label(image_frame, image=photo)
            img_label.image = photo
            img_label.pack()
        except:
            ttk.Label(image_frame, text="[Image unavailable]", style="Unit.TLabel").pack()

    # 6. Drag Function Dropdown (Row 2, Col 0-1)
    ttk.Label(main_frame, text="Drag Function", style="CustomLabel.TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    combo_drag = ttk.Combobox(
        main_frame,
        textvariable=drag_function_var,
        values=["G1", "G7"],
        state="readonly",
        width=10,
        justify='center',
        style="White.TCombobox",
    )
    combo_drag.config(font=(FONTS['family'], FONTS['label_size']))
    combo_drag.grid(row=2, column=1, sticky="w", padx=5, pady=2)
    combo_drag.current(0)

    # 7. Input Fields Defaults (Start at Row 3, Col 0-1)
    inputs = [
        ("Ballistic Coefficient", "bc", "0.314", ""),
        ("Bullet Weight", "weight", "143.00", "grn"),
        ("Muzzle Velocity", "v", "2970", "ft/s"),
        ("Barrel Twist", "twist", "8.00", "in [not utilized]"),
        ("Sight Height", "sight_height", "1.50", "in"),
        ("Shooting Angle", "shooting_angle", "0", "deg"),
        ("Zero Range", "zero_range", "100", "yd"),
        ("Wind Speed", "windspeed", "10", "mph"),
        ("Wind Angle", "windangle", "90", "deg"),
        ("Altitude", "altitude", "0", "ft"),
        ("Pressure", "barometer", "29.92", "inHg"),
        ("Temperature", "temperature", "59.0", "°F"),
        ("Humidity", "relative_humidity", "50.0", "%"),
    ]

    row = 3
    for label, key, default, unit in inputs:
        entry, err_lbl = create_row(main_frame, label, row, style_name="White.TEntry", default_val=default, unit=unit)
        fields[key] = entry
        error_labels[key] = err_lbl
        entry.bind("<FocusOut>", lambda e, k=key: validate_field(k, fields[k], error_labels[k]))
        row += 1

    # 8. Calculated Fields (Continue in Col 0-1)
    calc_fields = [
        ("Caliber / Diameter", "caliber", "0.0000", "in"),
        ("Cross-Sectional Area", "crs_sec_area", "0.0000", "in²"),
        ("Sectional Density", "sec_den", "0.0000", "lb/in²"),
    ]

    for label, key, default, unit in calc_fields:
        entry, err_lbl = create_row(main_frame, label, row, style_name="Gray.TEntry", default_val=default, unit=unit)
        fields[key] = entry
        error_labels[key] = err_lbl
        entry.config(state="readonly")
        row += 1

    # 9. Cartridge Selection Logic
    def update_on_cartridge_select(event=None):
        selected = cartridge_var.get()
        if not selected or selected not in cartridge_data:
            return
        data = cartridge_data[selected]

        fields["caliber"].config(state="normal")
        fields["caliber"].delete(0, tk.END)
        fields["caliber"].insert(0, f"{data['caliber']:.4f}")
        fields["caliber"].config(state="readonly")

        if "weight" in data and data["weight"] is not None:
            fields["weight"].config(state="normal")
            fields["weight"].delete(0, tk.END)
            fields["weight"].insert(0, f"{data['weight']:.2f}")
            fields["weight"].config(state="normal")

        if data.get("g7") is not None:
            drag_function_var.set("G7")
        elif data.get("g1") is not None:
            drag_function_var.set("G1")

        current_drag = drag_function_var.get()
        bc_val = data.get("g7") if current_drag == "G7" else data.get("g1")
        if bc_val is not None:
            fields["bc"].config(state="normal")
            fields["bc"].delete(0, tk.END)
            fields["bc"].insert(0, f"{bc_val:.4f}")
            fields["bc"].config(state="normal")

        if data.get("muzzle_velocity") is not None:
            fields["v"].config(state="normal")
            fields["v"].delete(0, tk.END)
            fields["v"].insert(0, f"{int(data['muzzle_velocity'])}")
            fields["v"].config(state="normal")

        calculate_ballistic_values(fields)

    combo_cartridge.bind("<<ComboboxSelected>>", update_on_cartridge_select)

    update_on_cartridge_select()

    # 10. Drag Function Change Logic
    def update_bc_on_drag(event=None):
        selected = cartridge_var.get()
        if not selected or selected not in cartridge_data:
            return
        data = cartridge_data[selected]
        current_drag = drag_function_var.get()
        bc_val = data.get("g7") if current_drag == "G7" else data.get("g1")
        if bc_val is not None:
            fields["bc"].config(state="normal")
            fields["bc"].delete(0, tk.END)
            fields["bc"].insert(0, f"{bc_val:.4f}")
            fields["bc"].config(state="normal")

    combo_drag.bind("<<ComboboxSelected>>", update_bc_on_drag)

    # 11. Weight Field Calculation Trigger
    fields["weight"].bind("<KeyRelease>", lambda event: calculate_ballistic_values(fields))

    # --- build the data dictionary for dataholder2 ---
    def get_form_data(fields, cartridge_var, drag_function_var):
        """Build the dictionary expected by dataholder2.add_run()."""
        return {
            "cartridge": cartridge_var.get(),
            "drag_function": drag_function_var.get(),
            "caliber": float(fields["caliber"].get()),
            "bc": float(fields["bc"].get()),
            "weight": float(fields["weight"].get()),
            "v": float(fields["v"].get()),
            "twist": float(fields["twist"].get()),
            "sight_height": float(fields["sight_height"].get()),
            "shooting_angle": float(fields["shooting_angle"].get()),
            "zero_range": float(fields["zero_range"].get()),
            "windspeed": float(fields["windspeed"].get()),
            "windangle": float(fields["windangle"].get()),
            "altitude": float(fields["altitude"].get()),
            "barometer": float(fields["barometer"].get()),
            "temperature": float(fields["temperature"].get()),
            "relative_humidity": float(fields["relative_humidity"].get()),
            "crs_sec_area": float(fields["crs_sec_area"].get()),
            "sec_den": float(fields["sec_den"].get()),
        }

    def toggle_menu():
        # Create the menu if it doesn't exist yet
        if not hasattr(root, '_app_menu'):
            root._app_menu = tk.Menu(root, tearoff=0,
                                     background=COLORS['bg_frame'],
                                     foreground=COLORS['label'],
                                     font=(FONTS['family'], FONTS['label_size']),
                                     borderwidth=0,
                                     relief="flat",
                                     activebackground=COLORS['gray'])

            # Define the helper function INSIDE the block so it has access to root._app_menu
            def close_and_show(title, msg):
                if hasattr(root, '_app_menu'):
                    try:
                        root._app_menu.unpost()
                    except:
                        pass
                show_dialog(title, msg)

            # help text with line breaks
            help_text = (
                "1. select a cartridge from the drop-down menu\n\n"
                "2a. for MFG rounds, ballistic coefficient, weight, and muzzle velocity will populate if known\n"
                "2b. for User Defined rounds, all data must be entered\n\n"
                "3. confirm the pre-populated data and adjust as appropriate\n\n"
                "4. revise the additional input parameters as required\n\n"
                "5. press the 'Add Round Data' button to store the information\n\n"
                "6a. press the 'Run Ballistics' button to kick off the calculator\n"
                "      or\n"
                "6b. enter new data for another 1 or 2 rounds\n\n"
                "[barrel twist is currently not utilized]"
            )

            # about text
            about_text = (
                "1. What is this?\n"
                "The Bcalc External Ballistics Calculator is an open-source external ballistics calculator that returns practical trajectory data without relying on cloud-based services.\n"
                "You can enter specific ammunition and environmental factors for up to three rounds.\n"
                "The calculator then produces, across multiple specified ranges:\n"
                ": output tables for trajectory metrics such as drop, wind drift, moa correction, moa wind, and velocity\n"
                ": three graphs comparing drop, velocity, and kinetic energy\n"
                ": text files containing all calculated metrics for integer ranges 1 to 800 yards\n"
                "An internet connection is not required once installed.\n"
                "No user data is collected or transmitted.\n\n"
               "2. Who is this for?\n"
                "Hunters and hobbyists.\n"
                "The calculator provides ballistics data for typical field and range scenarios with the ability to compare several rounds against one another.\n\n"
                "3. Who isn't this for?\n"
                "Long-range precision shooters.\n"
                "While the calculator returns good estimates for hunting and general recreation, it lacks the advanced modeling required for true long-range precision.  Check out Hornady's excellent 4DOF calculator if you are new to or considering long-range precision shooting.\n\n"
                "4. Why?\n"
                "I'm neither an external ballistics expert nor software developer.  The goals were to learn more about bullet trajectory (we are getting there) and learn python (slow going).  This calculator is a work in progress and provided for entertainment and educational purposes."
            )

            root._app_menu.add_command(label="About", command=lambda: close_and_show("About", about_text))
            root._app_menu.add_command(label="User Guide", command=lambda: close_and_show("User Guide", help_text))
            root._app_menu.add_command(label="Credits", command=lambda: close_and_show("Credits", "Bcalc External Ballistics Calculator\n\nCreated by Brian Calc.\n\nDraws heavily from the GNU Ballistics Calculator created by Derek Yates, updated by William Grim, and ported to python by Brad Rise.\n\nIn brief\n: created GUI Data Entry Form\n: added MFG ammunition data\n: included ability to compare rounds\n: revised several ballistic formulas\n: created GUI Results Screen"))
            root._app_menu.add_command(label="License", command=lambda: close_and_show("License", "GNU General Public License (GPL) Version 3."))
            root._app_menu.add_separator()
            root._app_menu.add_command(label="Exit", command=root.quit)

        # opening/closing the menu
        if getattr(menu_btn, '_menu_open', False):
            root._app_menu.unpost()
            menu_btn._menu_open = False
        else:
            menu_btn.update_idletasks()
            estimated_height = 150
            x_pos = menu_btn.winfo_rootx() - 30
            y_pos = menu_btn.winfo_rooty() - estimated_height

            if y_pos < 0:
                y_pos = 0

            root._app_menu.post(x_pos, y_pos)
            menu_btn._menu_open = True


    def show_dialog(title, message):
        try:
            dialog = tk.Toplevel(root)
            dialog.title(title)
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.configure(bg=COLORS['bg_frame'])

            # 1. Main Frame
            main_frame = ttk.Frame(dialog, style="CustomFrame.TFrame")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            # 2. Create Text Widget first (without scrollbar)
            text_widget = tk.Text(
                main_frame,
                wrap=tk.WORD,
                font=(FONTS['family'], 12),
                foreground=COLORS['label'],
                bg=COLORS['bg_frame'],
                selectbackground=COLORS['gray'],
                selectforeground=COLORS['label'],
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                padx=5,
                pady=5
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # 3. Insert text
            text_widget.insert(tk.END, message)
            text_widget.config(state=tk.DISABLED)

            # 4. Check if scrolling is needed
            # Get the number of lines in the text
            num_lines = int(text_widget.index('end-1c').split('.')[0])

            # If lines > 15 (approx height of window), show scrollbar
            if num_lines > 15:
                scrollbar = ttk.Scrollbar(main_frame, command=text_widget.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_widget.config(yscrollcommand=scrollbar.set)
                # Re-pack text to fill remaining space correctly
                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # 5. Close Button
            close_btn = ttk.Button(dialog, text="Close", command=dialog.destroy, bootstyle="primary")
            close_btn.pack(pady=(0, 15))

            dialog.transient(root)
            dialog.grab_set()
            dialog.wait_window()

        except Exception as e:
            print(f"[ERROR] show_dialog failed: {e}")
            messagebox.showinfo(title, message, parent=root)

    # 12. Store Button Logic
    def on_store():
        if store_count[0] >= 3:
            show_dialog("Limit Reached",
                        "3 rounds ready for comparison.\n\nClick 'Run Ballistics' to process.")
            add_button.configure(bootstyle="secondary")  #gray out the Add Round Data button
            add_button.config(state="disabled")
            return

        is_valid, errors = validate_all(fields, error_labels)
        if not is_valid:
            error_msg = "Please correct the following errors:\n\n" + "\n".join(errors)
            show_dialog("Validation Errors", error_msg)
            return

        # Build the data dictionary
        run_data = get_form_data(fields, cartridge_var, drag_function_var)

        # Send to dataholder2
        try:
            dataholder2.add_run(run_data)
        except ImportError:
            print("Warning: dataholder2 not found. Data not saved to module.")
        except Exception as e:
            print(f"Error adding run to dataholder2: {e}")

        # Update counter and UI
        store_count[0] += 1
        current_set = store_count[0]
        status_label.config(text=f"{current_set} of 3 rounds data stored")

        # Print to terminal
        print(f"\n--- STORED DATA: {current_set} OF 3 ROUNDS ---")
        print(f"Cartridge: {cartridge_var.get()}")
        print(f"Drag: {drag_function_var.get()}")
        for key, value in run_data.items():
            print(f"{key}: {value}")
        print(f"-----------------------------------------------\n")

    # 13. Execute Button Logic
    def on_execute():
        if store_count[0] < 1:
            show_dialog("No Data Stored",
                        "There must be data for at least 1 round before running ballistics.\n\n"
                        "Use the 'Add Round Data' button to stage the data.")
            return

        # clear dataholder2 to prepare for execution
        root.destroy()

    # Buttons
    btn_frame = ttk.Frame(main_frame, style="CustomFrame.TFrame")
    btn_frame.grid(row=row, column=0, columnspan=2, pady=20, sticky="w")

    add_button = ttk.Button(btn_frame, text="Add Round Data", bootstyle="primary", command=on_store)
    add_button.pack(side=LEFT, padx=5)
    ttk.Button(btn_frame, text="Run Ballistics", bootstyle="primary", command=on_execute).pack(side=LEFT, padx=5)

    # Status Label (Row row+1, Col 0-1, Left aligned)
    status_label = ttk.Label(main_frame, text="0 of 3 rounds data stored", foreground="green", font=(FONTS['family'], 12))
    status_label.grid(row=row+1, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Hamburger Menu Button (Row row+1, Col 2, Right aligned)
    # Using \u2261 for the hamburger icon (≡)
    menu_btn = ttk.Button(
        main_frame,
        text="\u2261",
        width=3,
        command=toggle_menu,
        style="TButton"
    )
    menu_btn.grid(row=row+1, column=2, sticky="e", padx=5, pady=(0, 10))


    root.mainloop()


if __name__ == "__main__":
    main()
