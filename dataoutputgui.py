# dataoutputgui.py
# output screen for Bcalc Ballistics Calculator

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Optional, Tuple
from tkinter import messagebox
import json
import os
import sys
import time
import csv
import math

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import (
    COLORS, FONTS, RANGE_OPTIONS, TABLE_METRICS,
    INPUT_PARAMS, ROUND_COLORS, ROUND_LABELS, FILES
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_RETRIES = 2
RETRY_DELAY = 0.02

def setup_styles(style):
    style.configure("TFrame", background=COLORS['bg_frame'])
    style.configure("TLabelframe", background=COLORS['bg_frame'])
    style.configure("TLabelframe.Label", foreground=COLORS['label'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['header_size'], "bold"))
    style.configure("CustomLabel.TLabel", foreground=COLORS['label'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['label_size']))
    style.configure("Unit.TLabel", foreground=COLORS['unit'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['unit_size']))
    style.configure("Title.TLabel", foreground=COLORS['error_text'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['title_size'], "bold"))
    style.configure("Section.TLabel", foreground=COLORS['label'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['header_size'], "bold"))
    style.configure("Header.TLabel", foreground=COLORS['label'],
                    background=COLORS['header_bg'],
                    font=(FONTS['family'], FONTS['label_size'], "bold"))
    style.configure("Small.TLabel", foreground=COLORS['label'],
                    background=COLORS['bg_frame'],
                    font=(FONTS['family'], FONTS['small_size']))
    style.configure("Data.TLabel", foreground=COLORS['label'],
                    background=COLORS['white'],
                    font=(FONTS['family'], FONTS['small_size']))
    style.configure("DataHeader.TLabel", foreground=COLORS['label'],
                    background=COLORS['gray'],
                    font=(FONTS['family'], FONTS['small_size'], "bold"))
    style.configure("TButton", font=(FONTS['family'], FONTS['label_size']))
    style.configure("TEntry", font=(FONTS['family'], FONTS['label_size']))
    style.configure("TCombobox", font=(FONTS['family'], FONTS['label_size']))


def load_json_file(filepath, retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Load a JSON file with retry logic."""
    for attempt in range(retries):
        try:
            if not os.path.exists(filepath):
                time.sleep(delay)
                continue
            if os.path.getsize(filepath) == 0:
                time.sleep(delay)
                continue
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    time.sleep(delay)
                    continue
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            time.sleep(delay)
    return None


def load_ndjson_file(filepath, retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Load an NDJSON file (one JSON object per line)."""
    for attempt in range(retries):
        try:
            if not os.path.exists(filepath):
                time.sleep(delay)
                continue
            if os.path.getsize(filepath) == 0:
                time.sleep(delay)
                continue
            records = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.lower() == "null":
                        continue
                    try:
                        obj = json.loads(stripped)
                        if (obj is None or not isinstance(obj, dict)
                                or 'range_yards' not in obj):
                            continue
                        records.append(obj)
                    except json.JSONDecodeError:
                        continue
            if records:
                return records
            time.sleep(delay)
        except IOError:
            time.sleep(delay)
    return None


def load_game_classification_rules(csv_path):
    #load datagameclass.csv to map
    rules = {}
    if not os.path.exists(csv_path):
        return rules
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                class_name = row.get('CLASS', 'Unknown')
                mappings = {
                    'TAYLOR': 'taylor_knockout',
                    'THORNILEY': 'thorniley',
                    'HAWKS': 'hawks',
                    'HITS': 'hornady_hits'
                }
                for csv_col, key in mappings.items():
                    range_str = row.get(csv_col)
                    if not range_str:
                        continue
                    try:
                        low_str, high_str = range_str.split('-')
                        low, high = float(low_str), float(high_str)
                        if key not in rules:
                            rules[key] = []
                        rules[key].append({
                            'low': low,
                            'high': high,
                            'desc': class_name
                        })
                    except ValueError:
                        continue
    except Exception:
        pass
    return rules


def find_closest_record(records, target_range):
    """Find the record in the list closest to the target range."""
    if not records:
        return None
    closest, min_diff = None, float('inf')
    for rec in records:
        ry = rec.get('range_yards')
        if ry is None:
            continue
        try:
            diff = abs(float(ry) - float(target_range))
            if diff < min_diff:
                min_diff, closest = diff, rec
        except (ValueError, TypeError):
            continue
    return closest


def format_value(val, decimals=None):
    """Format a numeric value with optional decimal places."""
    if val is None or val == '-':
        return "-"
    if decimals is not None:
        try:
            return f"{float(val):.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)
    return str(val)


def classify_metric(value, metric_key, rules):
    if metric_key not in rules:
        return format_value(value, 0)
    try:
        num_val = float(value)
    except (ValueError, TypeError):
        return str(value)
    for rule in rules.get(metric_key, []):
        if rule['low'] <= num_val <= rule['high']:
            return rule['desc']
        if rule['high'] == 9999 and num_val >= rule['low']:
            return rule['desc']
    return format_value(num_val, 0)



class BallisticsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bcalc External Ballistics")
        self.root.geometry("1400x820")
        self.root.option_add("*Font", (FONTS['family'], 10))

        self.ballistics_data = []
        self.term_data = []
        self.num_rounds = 0
        self.class_rules = {}
        self.graph_max_range = tk.IntVar(value=800)
        self.table_ranges = [
            tk.IntVar(value=50),
            tk.IntVar(value=100),
            tk.IntVar(value=800)
        ]
        self.fig = None
        self.canvas = None
        self.ax_drop = None
        self.ax_ke = None
        self.ax_vel = None
        self.quail_photo = None

        if not self.load_all_data():
            self.show_fatal_error()
            self.root.destroy()
            return

        style = ttk.Style()
        style.theme_use("litera")
        setup_styles(style)

        self.create_main_layout()
        self.setup_menu()

    def load_all_data(self):
        ballistics_path = os.path.join(SCRIPT_DIR, 'ballistics_runs.json')
        self.ballistics_data = load_json_file(ballistics_path)
        if not self.ballistics_data or not isinstance(self.ballistics_data, list):
            return False
        self.num_rounds = len(self.ballistics_data)
        if self.num_rounds == 0:
            return False

        self.term_data = []
        for i in range(1, self.num_rounds + 1):
            term_path = os.path.join(SCRIPT_DIR, f'term_run{i}.json')
            data = load_ndjson_file(term_path)
            self.term_data.append(data if data else [])

        csv_path = os.path.join(SCRIPT_DIR, 'datagameclass.csv')
        self.class_rules = load_game_classification_rules(csv_path)
        return True

    def show_fatal_error(self):
        msg = (
            "CRITICAL ERROR: Could not load data files.\n\n"
            f"Script Location: {SCRIPT_DIR}\n\n"
            "Check terminal output for details."
        )
        messagebox.showerror("Fatal Error", msg)

    def create_main_layout(self):
        """Create the 2x2 grid layout."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

        main_frame.columnconfigure(0, weight=0, minsize=280)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=4)

        self.create_section_cartridges(main_frame)
        self.create_section_inputs(main_frame)
        self.create_section_table(main_frame)
        self.create_section_graphs(main_frame)

    def create_section_cartridges(self, parent):
        """Create Section 1: Cartridges list."""
        frame = ttk.LabelFrame(parent, text="Cartridges")
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 5))


        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=0)

        for i in range(self.num_rounds):
            round_num = i + 1
            cartridge_name = self.ballistics_data[i].get('cartridge', 'N/A')

            # Label "Round 1:"
            ttk.Label(frame, text=f"Round {round_num}:",
                      style="CustomLabel.TLabel").grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=2)

            # Label "Cartridge Name" - Added padx=(10, 0) for the gap
            ttk.Label(frame, text=str(cartridge_name),
                      style="CustomLabel.TLabel").grid(
                row=i, column=1, sticky="w", padx=(10, 0), pady=2)

        #load the Quail Image at the bottom left of the Cartridge section

        self.load_quail_image(frame)

    def create_section_inputs(self, parent):
        """Create Section 2: Input Parameters grid."""
        self.input_frame = ttk.LabelFrame(parent, text="Input Parameters")
        self.input_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(5, 0))
        self.input_frame.columnconfigure(0, weight=0)
        for j in range(self.num_rounds):
            self.input_frame.columnconfigure(j+1, weight=1)

        ttk.Label(self.input_frame, text="", style="Unit.TLabel", width=18).grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        for j in range(self.num_rounds):
            ttk.Label(self.input_frame, text=f"Round {j+1}", style="Header.TLabel",
                      width=12, anchor="center").grid(
                row=0, column=j+1, sticky="ew", padx=2, pady=(0, 4))

        for row_idx, (key, display_name, decimals) in enumerate(INPUT_PARAMS):
            ttk.Label(self.input_frame, text=f"{display_name}:", style="Small.TLabel",
                      width=18, anchor="w").grid(
                row=row_idx+1, column=0, sticky="w", pady=1)
            for j in range(self.num_rounds):
                val = self.ballistics_data[j].get(key, "N/A")
                formatted = format_value(val, decimals)
                ttk.Label(self.input_frame, text=formatted, style="Small.TLabel",
                          width=12, anchor="center").grid(
                    row=row_idx+1, column=j+1, sticky="ew", padx=2, pady=1)

    def create_section_table(self, parent):
        """Create Section 3: Trajectory Data Table with vertical scrollbar."""
        frame = ttk.LabelFrame(parent, text="Trajectory Data")
        frame.grid(row=0, column=1, sticky="nsew", pady=0)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        inner = ttk.Frame(frame)
        inner.pack(fill=BOTH, expand=True, padx=5, pady=5)
        inner.columnconfigure(0, weight=1)
        inner.rowconfigure(0, weight=1)

        # Create Canvas and Vertical Scrollbar
        self.table_canvas = tk.Canvas(inner, bg=COLORS['white'], highlightthickness=0)
        self.table_scrollbar = ttk.Scrollbar(inner, orient="vertical",
                                             command=self.table_canvas.yview)

        self.table_canvas.configure(yscrollcommand=self.table_scrollbar.set)

        # Grid layout: Canvas takes left, Scrollbar takes right
        self.table_scrollbar.grid(row=0, column=1, sticky="ns")
        self.table_canvas.grid(row=0, column=0, sticky="nsew")

        # Create the table frame INSIDE the canvas
        self.table_frame = ttk.Frame(self.table_canvas)

        # Create a window in the canvas to hold the frame
        self.table_canvas_window = self.table_canvas.create_window(
            (0, 0), window=self.table_frame, anchor="nw")

        # Bind events
        self.table_frame.bind("<Configure>", self.on_table_frame_configure)
        self.table_canvas.bind("<Configure>", self.on_table_canvas_configure)

        # Initial draw
        self.update_table_display()

    def on_table_frame_configure(self, event=None):
        """Update scroll region when the table frame changes size."""
        self.table_canvas.configure(
            scrollregion=self.table_canvas.bbox("all"))

    def on_table_canvas_configure(self, event=None):
        """Resize the inner frame width to match the canvas width."""
        canvas_width = event.width
        self.table_canvas.itemconfig(
            self.table_canvas_window, width=canvas_width)

    def update_table_display(self):
        """Rebuild the table. Dropdowns act as the range headers."""
        # 1. Clear everything
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        ranges = [self.table_ranges[i].get() for i in range(3)]
        num_ranges = len(ranges)
        total_cols = num_ranges * self.num_rounds

        # --- ROW 0: Headers ---

        # Column 0: "Metric" Label
        ttk.Label(self.table_frame, text="Metric",
                  style="DataHeader.TLabel", width=16, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=2, pady=2)

        col_offset = 1
        for i in range(3): # Always 3 ranges
            rng = ranges[i]

            # Create a container frame for this column header
            header_frame = ttk.Frame(self.table_frame)
            header_frame.grid(row=0, column=col_offset, columnspan=self.num_rounds,
                              sticky="ew", padx=2, pady=2)

            # 1. The Dropdown (The Range Header)
            combo = ttk.Combobox(header_frame,
                                 textvariable=self.table_ranges[i],
                                 values=RANGE_OPTIONS,
                                 state="readonly",
                                 width=6,
                                 justify='center')
            combo.pack(side="top", fill="x", padx=1, pady=1)

            # Bind the event to redraw
            combo.bind("<<ComboboxSelected>>", lambda e, idx=i: self.update_table_display())

            # 2. The Round Labels (R1, R2, R3) below the dropdown
            for j in range(self.num_rounds):
                lbl = ttk.Label(header_frame, text=f"R{j+1}",
                                style="DataHeader.TLabel", width=6, anchor="center")
                lbl.pack(side="left", fill="x", expand=True, padx=1)

            col_offset += self.num_rounds

        #force update scroll region
        self.on_table_frame_configure()

        # Separator
        ttk.Separator(self.table_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=1 + total_cols, sticky="ew", pady=2)

        # --- DATA ROWS (Start at Row 2) ---
        for row_idx, (metric_key, metric_name, decimals) in enumerate(TABLE_METRICS):
            # Metric Name
            ttk.Label(self.table_frame, text=metric_name,
                      style="Small.TLabel", width=16, anchor="w").grid(
                row=row_idx + 2, column=0, sticky="w", padx=2, pady=2)

            col_offset = 1
            for rng in ranges:
                for j in range(self.num_rounds):
                    records = self.term_data[j] if j < len(self.term_data) else []
                    closest = find_closest_record(records, rng)

                    if closest is None:
                        display_val = "-"
                    else:
                        if metric_key in ('ke', 'momentum', 'taylor_knockout',
                                          'thorniley', 'hawks', 'hornady_hits'):
                            raw_val = closest.get('results', {}).get(metric_key, None)
                        else:
                            raw_val = closest.get(metric_key, None)

                        if metric_key in ('taylor_knockout', 'thorniley',
                                          'hawks', 'hornady_hits'):
                            display_val = classify_metric(raw_val, metric_key, self.class_rules)
                        else:
                            display_val = format_value(raw_val, decimals)

                    ttk.Label(self.table_frame, text=display_val,
                              style="Data.TLabel", width=9, anchor="center").grid(
                        row=row_idx + 2, column=col_offset, sticky="ew", padx=1, pady=2)
                    col_offset += 1

    def create_section_graphs(self, parent):
        """Create Section 4: Graphs with shared range control."""
        frame = ttk.LabelFrame(parent, text="Graphs")
        frame.grid(row=1, column=1, sticky="nsew", pady=(5, 0))
        frame.columnconfigure(0, weight=1)

        ctrl_row = ttk.Frame(frame)
        ctrl_row.pack(fill=X, pady=(0, 10))
        ttk.Label(ctrl_row, text="Max Range:",
                  style="Section.TLabel").pack(side=LEFT, padx=(0, 10))

        self.graph_combo = ttk.Combobox(
            ctrl_row,
            textvariable=self.graph_max_range,
            values=RANGE_OPTIONS,
            state="readonly",
            width=8
        )
        self.graph_combo.pack(side=LEFT)
        self.graph_combo.bind("<<ComboboxSelected>>", self.update_graphs)

        graph_container = ttk.Frame(frame)
        graph_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax_drop = self.fig.add_subplot(311)
        self.ax_ke = self.fig.add_subplot(312)
        self.ax_vel = self.fig.add_subplot(313)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.update_graphs()

    def update_graphs(self, event=None):
        """Update all three graphs based on selected max range."""
        max_range = self.graph_max_range.get()
        self.ax_drop.clear()
        self.ax_ke.clear()
        self.ax_vel.clear()

        for i, term_data in enumerate(self.term_data):
            if i >= len(ROUND_COLORS):
                break
            color, label = ROUND_COLORS[i], ROUND_LABELS[i]

            pts = [(item.get('range_yards'), item)
                   for item in term_data
                   if item.get('range_yards') is not None]
            try:
                pts.sort(key=lambda x: float(x[0]))
            except Exception:
                pass

            aligned_ranges = []
            aligned_drop = []
            aligned_ke = []
            aligned_vel = []

            for rng, item in pts:
                try:
                    xr = float(rng)
                except (ValueError, TypeError):
                    continue
                if xr > max_range:
                    continue

                drop = item.get('drop_in')
                ke = item.get('results', {}).get('ke')
                vel = item.get('velocity_ft_s')

                if drop is not None:
                    aligned_ranges.append(xr)
                    aligned_drop.append(float(drop))
                    aligned_ke.append(float(ke) if ke is not None else None)
                    aligned_vel.append(float(vel) if vel is not None else None)

            if aligned_ranges:
                self.ax_drop.plot(aligned_ranges, aligned_drop,
                                  color=color, label=label, linewidth=2)

                valid_ke = [(r, k) for r, k in
                            zip(aligned_ranges, aligned_ke)
                            if k is not None]
                if valid_ke:
                    k_r, k_v = zip(*valid_ke)
                    self.ax_ke.plot(k_r, k_v, color=color,
                                    label=label, linewidth=2)

                valid_vel = [(r, v) for r, v in
                             zip(aligned_ranges, aligned_vel)
                             if v is not None]
                if valid_vel:
                    v_r, v_v = zip(*valid_vel)
                    self.ax_vel.plot(v_r, v_v, color=color,
                                    label=label, linewidth=2)

        self.format_axis(self.ax_drop, "Drop")
        self.format_axis(self.ax_ke, "KE")
        self.format_axis(self.ax_vel, "Velocity")

        for ax in [self.ax_drop, self.ax_ke, self.ax_vel]:
            ax.set_xlim(0, max_range)
            ax.set_xticks(list(range(0, max_range + 1, 50)))
            ax.grid(True, which='major', alpha=0.4)
            ax.grid(True, which='minor', alpha=0.2)
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.legend(loc='best', fontsize=9)

        if max_range <= 75:
            for ax in [self.ax_drop, self.ax_ke, self.ax_vel]:
                ticks = list(range(0, max_range + 1, 25))
                ax.set_xticks(ticks)
                if len(ticks) > 1:
                    labels = ['0'] + [''] * (len(ticks) - 2) + [str(max_range)]
                else:
                    labels = ['0']
                ax.set_xticklabels(labels)

        self.fig.tight_layout(pad=0.5)
        self.fig.subplots_adjust(hspace=0.35)
        self.canvas.draw()

    def format_axis(self, ax, ylabel):
        ax.set_ylabel(ylabel, fontsize=10)

    def load_quail_image(self, parent):
        #load and display the quail silhouette image
        img_path = os.path.join(SCRIPT_DIR, "bcalcexticon.png")
        if not os.path.exists(img_path):
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(img_path)
            img.thumbnail((100, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.quail_photo = photo
            ttk.Label(parent, image=photo, background="white").place(
                relx=0.05, rely=0.95, anchor=tk.SW)
        except ImportError:
            pass
        except Exception:
            pass

    def setup_menu(self):
        #create hamburger menu
        self.menu_btn = ttk.Button(
            self.root, text="\u2261", width=3,
            command=self.toggle_menu, style="TButton")
        self.menu_btn.place(in_=self.input_frame, relx=0.05, rely=1.0, anchor=tk.SW, y=-5)

        self.app_menu = tk.Menu(
            self.root, tearoff=0,
            background=COLORS['bg_frame'],
            foreground=COLORS['label'],
            font=(FONTS['family'], FONTS['label_size']),
            borderwidth=0, relief="flat",
            activebackground=COLORS['gray'])

        def close_and_show(title, msg):
            try:
                self.app_menu.unpost()
            except Exception:
                pass
            self.show_dialog(title, msg)

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

        credits_text = (
            "Bcalc External Ballistics Calculator\n\nCreated by Brian Calc.\n\n"
            "Draws heavily from the GNU Ballistics Calculator created by Derek Yates, "
            "updated by William Grim, and ported to python by Brad Rise.\n\n"
            "In brief\n: created GUI Data Entry Form\n: added MFG ammunition data\n: included ability to compare rounds\n: revised several ballistic formulas\n: created GUI Results Screen")
        license_text = "GNU General Public License (GPL) Version 3."

        self.app_menu.add_command(label="Save Results", command=self.print_results)
        self.app_menu.add_command(label="Enter New Data", command=self.close_to_entry)
        self.app_menu.add_command(label="Exit Program", command=self.exit_app)
        self.app_menu.add_separator()
        self.app_menu.add_command(label="About", command=lambda: close_and_show("About", about_text))
        self.app_menu.add_command(label="Credits", command=lambda: close_and_show("Credits", credits_text))
        self.app_menu.add_command(label="License", command=lambda: close_and_show("License", license_text))

    def toggle_menu(self):
        if getattr(self.menu_btn, '_menu_open', False):
            self.app_menu.unpost()
            self.menu_btn._menu_open = False
        else:
            self.menu_btn.update_idletasks()
            x_pos = self.menu_btn.winfo_rootx() + 5
            y_pos = self.menu_btn.winfo_rooty() - 200
            if y_pos < 0:
                y_pos = 0
            self.app_menu.post(x_pos, y_pos)
            self.menu_btn._menu_open = True

    def show_dialog(self, title, message):
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.configure(bg=COLORS['bg_frame'])

            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            text_widget = tk.Text(
                frame, wrap=tk.WORD,
                font=(FONTS['family'], 12),
                foreground=COLORS['label'],
                bg=COLORS['bg_frame'],
                selectbackground=COLORS['gray'],
                selectforeground=COLORS['label'],
                relief="flat", borderwidth=0,
                highlightthickness=0,
                padx=5, pady=5)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            text_widget.insert(tk.END, message)
            text_widget.config(state=tk.DISABLED)

            num_lines = int(text_widget.index('end-1c').split('.')[0])
            if num_lines > 15:
                scrollbar = ttk.Scrollbar(frame, command=text_widget.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_widget.config(yscrollcommand=scrollbar.set)

            ttk.Button(dialog, text="Close", command=dialog.destroy,
                       bootstyle="primary").pack(pady=(0, 15))

            dialog.transient(self.root)
            dialog.grab_set()
            dialog.wait_window()
        except Exception as e:
            print(f"[ERROR] show_dialog failed: {e}")
            messagebox.showinfo(title, message, parent=self.root)

    def print_results(self):
        """Capture the window and save data files to user's Documents folder."""
        try:
            from PIL import ImageGrab
            import os
            from pathlib import Path
            from datetime import datetime
            import shutil

            # 1. Setup Paths
            home = Path.home()
            documents = home / "Documents"
            documents.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"BcalcResults_{timestamp}"

            # 2. Identify Files to Save
            files_to_save = []
            for i in range(1, 4):
                src_path = Path(SCRIPT_DIR) / f"term_run{i}.json"
                if src_path.exists():
                    files_to_save.append({
                        "src": src_path,
                        "dest_name": f"{base_filename}_run{i}.json",
                        "type": "data"
                    })

            # 3. Confirmation Dialog
            confirm_lines = [
                f"Will save to your Documents folder:\n\n"
                f"Screenshot: {base_filename}.png"
            ]
            for f in files_to_save:
                confirm_lines.append(f"Text File: {f['dest_name']}")

            confirm_lines.append("\nYes to save or No to cancel.")

            if not messagebox.askyesno("Save Results", "\n".join(confirm_lines)):
                return

            # 4. Wait for dialog to close
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.5)
            self.root.update_idletasks()
            self.root.update()

            # --- SAVE SCREENSHOT ---
            x = self.root.winfo_rootx()
            y = self.root.winfo_rooty()
            w = self.root.winfo_width()
            h = self.root.winfo_height()

            if w <= 0 or h <= 0:
                messagebox.showerror("Error", "Window size is invalid. Please resize the window.")
                return

            screenshot_path = documents / f"{base_filename}.png"
            try:
                screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                    raise ValueError("Empty screenshot")
                screenshot.save(str(screenshot_path), 'PNG')
                screenshot_success = True
                print(f"[INFO] Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"[ERROR] Screenshot failed: {e}")
                screenshot_success = False

            # --- COPY JSON FILES ---
            saved_count = 0
            failed_count = 0
            failed_files = []

            for file_info in files_to_save:
                dest_path = documents / file_info["dest_name"]
                try:
                    shutil.copy2(str(file_info["src"]), str(dest_path))
                    saved_count += 1
                    print(f"[INFO] Data file saved: {dest_path}")
                except Exception as e:
                    failed_count += 1
                    failed_files.append(file_info["dest_name"])
                    print(f"[ERROR] Failed to copy {file_info['src']}: {e}")

            # 5. Final Report
            total_expected = 1 + len(files_to_save)
            total_saved = (1 if screenshot_success else 0) + saved_count

            if total_saved == total_expected:
                msg = f"Saved {total_saved} file(s) to your Documents folder."
                msg_type = "info"
            else:
                msg = f"Saved {total_saved} of {total_expected} files.\n\n"
                if not screenshot_success:
                    msg += "- Screenshot failed to save.\n"
                if failed_count > 0:
                    msg += f"- {failed_count} data file(s) failed to save:\n"
                    for f in failed_files:
                        msg += f"  - {f}\n"
                msg_type = "warning"

            messagebox.showinfo("Save Complete" if msg_type == "info" else "Partial Save", msg)

        except ImportError:
            messagebox.showerror("Missing Dependency",
                                 "Pillow is required for screenshots.\n"
                                 "Install with: pip install Pillow")
        except PermissionError:
            messagebox.showerror("Permission Error",
                                 f"Cannot write to Documents folder.\n"
                                 f"Please check permissions for:\n{documents}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Unexpected error occurred:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def close_to_entry(self):
        """Close this window and restart startprogram.py to enter new data."""
        print("[INFO] User chose 'Enter New Data'. Restarting main program.")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "startprogram.py")

        if not os.path.exists(start_script):
            messagebox.showerror("Error", "Could not find startprogram.py to restart.")
            return

        try:
            os.execlp(sys.executable, sys.executable, start_script)
            # If execlp succeeds, the code below never runs.
            # If it fails, we fall through to the error handling.
        except Exception as e:
            print(f"[ERROR] Failed to restart startprogram.py: {e}")
            messagebox.showerror("Error", f"Failed to restart: {e}")

    def exit_app(self):
        if messagebox.askyesno("Exit",
                               "Confirming you want to exit?"):
            print("[INFO] User chose 'Exit'. Shutting down.")
            self.root.destroy()
            sys.exit(0)

def main():
    try:
        print("[GUI] Initializing Bcalc Results Window...")
        root = ttk.Tk()
        app = BallisticsGUI(root)
        print("[GUI] Window created successfully. Starting main loop.")
        root.mainloop()
    except tk.TclError as e:
        print(f"[CRITICAL GUI ERROR] Tkinter/Tcl Error: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"[CRITICAL GUI ERROR] Import Error: {e}")
        print("Missing library? Try: pip install ttkbootstrap matplotlib pillow")
        sys.exit(1)
    except Exception as e:
        print(f"[CRITICAL GUI ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
