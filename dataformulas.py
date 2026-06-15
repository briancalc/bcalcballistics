#dataformulas.py
"""
Reads ballistics_runs.json and trac_runN.json files
For each non-null trac line, computes six ballistic metrics using the
formulas provided and appends a "results" object to the line before
writing to term_runN.json. Null lines are preserved.
"""
from __future__ import annotations
import json
import os
import math
from dataclasses import dataclass, asdict
from typing import List, Optional

GRAINS_PER_POUND = 7000.0
KE_DIVISOR = 450437.0
THORNILEY_CONSTANT = 2.866
HORNADY_HITS_DIVISOR = 700000.0


@dataclass(frozen=True)
class BallFormulas:
    weight: float
    vel_dataform: float
    caliber: float
    crs_sec_area: float
    sec_den: float


@dataclass(frozen=True)
class BallResults:
    ke: float
    momentum: float
    taylor_knockout: float
    thorniley: float
    hawks: float
    hornady_hits: float


def ke(weight: float, vel_dataform: float) -> float:
    return (weight * vel_dataform ** 2) / KE_DIVISOR


def mo(weight: float, vel_dataform: float) -> float:
    return (weight / GRAINS_PER_POUND) * vel_dataform


def taylor_knockout_factor(weight: float, vel_dataform: float, caliber: float) -> float:
    return (weight / GRAINS_PER_POUND) * vel_dataform * caliber


def thorniley_stopping_power(weight: float, vel_dataform: float, caliber: float) -> float:
    return (THORNILEY_CONSTANT * vel_dataform) * (weight / GRAINS_PER_POUND) * math.sqrt(caliber)


def hawks_killing_power(ke_val: float, crs_sec_area: float, sec_den: float) -> float:
    return ke_val * crs_sec_area * sec_den


def hornady_hits(weight: float, vel_dataform: float, caliber: float) -> float:
    return ((weight * weight * vel_dataform) / (caliber * caliber)) / HORNADY_HITS_DIVISOR


def compute_run(run: BallFormulas) -> BallResults:
    ke_val = ke(run.weight, run.vel_dataform)
    return BallResults(
        ke=round(ke_val, 4),
        momentum=round(mo(run.weight, run.vel_dataform), 4),
        taylor_knockout=round(taylor_knockout_factor(run.weight, run.vel_dataform, run.caliber), 2),
        thorniley=round(thorniley_stopping_power(run.weight, run.vel_dataform, run.caliber), 2),
        hawks=round(hawks_killing_power(ke_val, run.crs_sec_area, run.sec_den), 2),
        hornady_hits=round(hornady_hits(run.weight, run.vel_dataform, run.caliber), 2),
    )


def load_ballistics_runs(path: str = "ballistics_runs.json") -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("ballistics_runs.json must contain a JSON array")
    return data


def find_trac_files() -> List[int]:
    found = []
    for n in (1, 2, 3):
        name = f"trac_run{n}.json"
        if os.path.isfile(name):
            found.append(n)
    return found


def write_atomic(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def find_ballistics_entry(ballistics: List[dict], run_number: int) -> Optional[dict]:
    for entry in ballistics:
        rn = entry.get("run_number")
        if isinstance(rn, int) and rn == run_number:
            return entry
    return None


def safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except Exception:
        return None


def process_trac_run(n: int, ballistics: List[dict]) -> int:
    trac_name = f"trac_run{n}.json"
    out_name = f"term_run{n}.json"
    processed_lines = 0
    written_lines = 0

    entry = find_ballistics_entry(ballistics, n)
    if entry is None:
        print(f"[FATAL] No entry in ballistics_runs.json with run_number == {n}")
        return 1

    # Validate required constant fields for this run
    required_fields = ["weight", "caliber", "crs_sec_area", "sec_den"]
    missing = [f for f in required_fields if safe_float(entry.get(f)) is None]
    if missing:
        print(f"[FATAL] Missing or invalid required fields for run {n}: {missing}")
        return 1

    # prepare constant values
    weight = float(entry["weight"])
    caliber = float(entry["caliber"])
    crs_sec_area = float(entry["crs_sec_area"])
    sec_den = float(entry["sec_den"])

    out_lines: List[str] = []

    try:
        with open(trac_name, "r", encoding="utf-8") as f:
            for idx, raw in enumerate(f, start=1):
                processed_lines += 1
                line = raw.strip()
                if line == "" or line.lower() == "null":
                    # preserve literal null or blank as null
                    out_lines.append("null")
                    written_lines += 1
                    continue
                try:
                    obj = json.loads(line)
                    # Expect velocity_ft_s present and numeric
                    vel = safe_float(obj.get("velocity_ft_s"))
                    if vel is None:
                        print(f"[ERROR] Run {n}, line {idx}: missing/invalid velocity_ft_s -> writing null")
                        out_lines.append("null")
                        written_lines += 1
                        continue

                    # build input dataclass and compute
                    run_input = BallFormulas(
                        weight=weight,
                        vel_dataform=float(vel),
                        caliber=caliber,
                        crs_sec_area=crs_sec_area,
                        sec_den=sec_den,
                    )
                    results = compute_run(run_input)
                    # append results object
                    obj_out = dict(obj)  # shallow copy of original fields
                    obj_out["results"] = asdict(results)
                    out_lines.append(json.dumps(obj_out, ensure_ascii=False))
                    written_lines += 1
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Run {n}, line {idx}: JSON parse error: {e.msg} -> writing null")
                    out_lines.append("null")
                    written_lines += 1
    except Exception as e:
        print(f"[FATAL] Error reading {trac_name}: {e}")
        return 1

    # write output NDJSON atomically
    try:
        write_atomic(out_name, "\n".join(out_lines) + "\n")
    except Exception as e:
        print(f"[FATAL] Error writing {out_name}: {e}")
        return 1

    # summary to terminal
    print(f"Run {n}: processed {processed_lines} lines, wrote {written_lines} lines -> {out_name}")
    return 0


def main() -> int:
    try:
        ballistics = load_ballistics_runs("ballistics_runs.json")
    except Exception as e:
        print(f"[FATAL] Unable to read ballistics_runs.json: {e}")
        return 2

    # determine declared runs from ballistics_runs.json
    declared_runs = set()
    for entry in ballistics:
        rn = entry.get("run_number")
        if isinstance(rn, int):
            declared_runs.add(rn)

    # remove any old term_run files for runs that are not declared
    for n in (1, 2, 3):
        if n not in declared_runs:
            stale_out = f"term_run{n}.json"
            try:
                if os.path.isfile(stale_out):
                    os.remove(stale_out)
                    print(f"[CLEANUP] removed stale file: {stale_out}")
            except Exception as e:
                print(f"[WARN] failed to remove {stale_out}: {e}")

    found = find_trac_files()
    if not found:
        print("No trac_runN.json files found (N=1..3). Nothing to do.")
        return 0

    exit_code = 0
    for n in found:
        if n not in declared_runs:
            #skip stale trac files that don't match current ballistics_runs.json
            print(f"[SKIP] trac_run{n}.json found but no matching run_number in ballistics_runs.json; skipped.")
            continue

        rc = process_trac_run(n, ballistics)
        if rc != 0:
            exit_code = rc  #return non-zero if any run had fatal issue

    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
