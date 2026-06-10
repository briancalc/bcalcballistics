# dataholder.py

import csv
from typing import Dict, Optional

def load_cartridge_data(filename: str) -> Dict[str, Dict]:
    """
    Loads cartridge data from a CSV file.
    Args: filename: Path to the CSV file containing CARTRIDGE, CALIBER, G1, G7, Weight, and muzzle velocity columns.
    Returns: Dict mapping cartridge name (str) to a dict containing:
            - 'caliber': float
            - 'g1': float or None
            - 'g7': float or None
            - 'weight': float or None
            -muzzle':float or none'
    Raises:FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing or data cannot be parsed.
    """
    data: Dict[str, Dict] = {}

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers.")

        # Normalize headers (case-insensitive)
        headers = {h.lower(): h for h in reader.fieldnames}

        cartridge_key = headers.get("cartridge")
        caliber_key = headers.get("caliber")
        g1_key = headers.get("g1")
        g7_key = headers.get("g7")
        weight_key = headers.get("weight")
        muzzle_key = headers.get("muzzle")

        if not cartridge_key or not caliber_key:
            raise ValueError(
                "CSV must contain 'CARTRIDGE' and 'CALIBER' columns (case-insensitive)."
            )

        for row_num, row in enumerate(reader, start=2):
            cartridge = row[cartridge_key].strip()

            # Parse Caliber (Required)
            try:
                caliber = float(row[caliber_key].strip())
            except ValueError:
                raise ValueError(
                    f"Row {row_num}: Caliber value '{row[caliber_key]}' is not a valid number."
                )

            # Parse Optional Fields (G1, G7, Weight)
            g1_val = None
            g7_val = None
            weight_val = None
            muzzle_val = None

            if g1_key and row[g1_key].strip():
                try:
                    g1_val = float(row[g1_key].strip())
                except ValueError:
                    pass

            if g7_key and row[g7_key].strip():
                try:
                    g7_val = float(row[g7_key].strip())
                except ValueError:
                    pass

            if weight_key and row[weight_key].strip():
                try:
                    weight_val = float(row[weight_key].strip())
                except ValueError:
                    pass

            if muzzle_key and row[muzzle_key].strip():
                try:
                    muzzle_val = float(row[muzzle_key].strip())
                except ValueError:
                    pass

            if not cartridge:
                raise ValueError(f"Row {row_num}: Cartridge name is empty.")

            data[cartridge] = {
                "caliber": caliber,
                "g1": g1_val,
                "g7": g7_val,
                "weight": weight_val,
                "muzzle_velocity": muzzle_val
            }

    return data
