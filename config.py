# config.py - Centralized application configuration

# ============================================
# COLORS
# ============================================
COLORS = {
    'bg_frame': "#FFFFFF",
    'label': "#333333",
    'white': "#FFFFFF",
    'gray': "#D3D3D3",
    'error_bg': "#FFCDD2",
    'error_text': "#D32F2F",
    'unit': "#999999",
    'header_bg': "#F5F5F5",
}

# ============================================
# FONTS
# ============================================
FONTS = {
    'family': "Roboto",
    'label_size': 12,
    'unit_size': 10,
    'title_size': 16,
    'header_size': 13,
    'small_size': 10,
}

# ============================================
# BALLISTICS CONSTANTS
# ============================================
GRAVITY = -32.194
BALLISTICS_COMPUTATION_MAX_YARDS = 801
MAX_OUTPUT_RANGE_YARDS = 800

# Predefined range options for dropdowns/tables
RANGE_OPTIONS = [25, 50, 75, 100, 150, 200, 250, 300, 350, 400,
                 450, 500, 550, 600, 650, 700, 750, 800]

# Output ranges for terminal printing (from ballistics.py)
OUTPUT_RANGES = [100, 400, 800]

# ============================================
# FILE PATHS
# ============================================
FILES = {
    'ballistics_runs': 'ballistics_runs.json',
    'trac_run_pattern': 'trac_run{}.json',
    'term_run_pattern': 'term_run{}.json',
    'cartridge_csv': 'datacartcal.csv',
    'game_class_csv': 'datagameclass.csv',
    'icon_image': 'bcalcexticon.png',
    'debug_log': 'debug_output.txt',
}

# ============================================
# INPUT PARAMETERS (For Data Entry Form)
# ============================================
INPUT_PARAMS = [
    ("caliber", "Caliber", 3),
    ("drag_function", "Drag Function", None),
    ("bc", "Ballistic Coefficient", 3),
    ("weight", "Bullet Weight", 1),
    ("v", "Muzzle Velocity", 0),
    ("sight_height", "Sight Height", 2),
    ("twist", "Barrel Twist", 2),
    ("shooting_angle", "Shooting Angle", 0),
    ("zero_range", "Zero Range", 0),
    ("windspeed", "Wind Speed", 0),
    ("windangle", "Wind Angle", 0),
    ("altitude", "Altitude", 0),
    ("barometer", "Pressure", 2),
    ("temperature", "Temperature", 0),
    ("relative_humidity", "Humidity", 1),
]

# ============================================
# TABLE METRICS (For Results Display)
# ============================================
TABLE_METRICS = [
    ("drop_in", "Drop (in)", 2),
    ("wind_drift_in", "Wind Drift (in)", 2),
    ("moa_correction", "MOA Correction", 2),
    ("wind_moa_correction", "Wind MOA", 2),
    ("velocity_ft_s", "Velocity (ft/s)", 0),
    ("tof_seconds", "TOF (s)", 2),
    ("ke", "Kinetic Energy", 0),
    ("momentum", "Momentum", 2),
    ("taylor_knockout", "Taylor KO", 0),
    ("thorniley", "Thorniley", 0),
    ("hawks", "Hawks", 0),
    ("hornady_hits", "Hornady HITS", 0),
]

# ============================================
# VALIDATION RULES
# ============================================
VALIDATION_RULES = {
    "bc": (0.1, 2.0),
    "weight": (1, 600),
    "v": (100, 5000),
    "twist": (1, 10),
    "sight_height": (0, 5),
    "shooting_angle": (-35, 35),
    "zero_range": (0, 800),
    "windspeed": (0, 50),
    "windangle": (0, 359),
    "altitude": (-1000, 10000),
    "barometer": (20, 35),
    "temperature": (-30, 130),
    "relative_humidity": (0, 100),
}

# ============================================
# ROUND COLORS FOR GRAPHING
# ============================================
ROUND_COLORS = ['red', 'blue', 'green']
ROUND_LABELS = ['Round 1', 'Round 2', 'Round 3']
