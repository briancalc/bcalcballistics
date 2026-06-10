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
import time
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


def append_log(log_path: str, lines: List[str]) -> None:
    tmp = log_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, log_path)


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
    log_name = f"term_run{n}_errors.log"
    errors: List[str] = []
    processed_lines = 0
    written_lines = 0

    entry = find_ballistics_entry(ballistics, n)
    if entry is None:
        errors.append(f"[FATAL] No entry in ballistics_runs.json with run_number == {n}")
        append_log(log_name, header_log(n, errors))
        return 1

    # Validate required constant fields for this run
    required_fields = ["weight", "caliber", "crs_sec_area", "sec_den"]
    missing = [f for f in required_fields if safe_float(entry.get(f)) is None]
    if missing:
        errors.append(f"[FATAL] Missing or invalid required fields for run {n}: {missing}")
        append_log(log_name, header_log(n, errors))
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
                        errors.append(f"Line {idx}: missing/invalid velocity_ft_s -> writing null")
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
                    errors.append(f"Line {idx}: JSON parse error: {e.msg} -> writing null")
                    out_lines.append("null")
                    written_lines += 1
    except Exception as e:
        errors.append(f"[FATAL] Error reading {trac_name}: {e}")
        append_log(log_name, header_log(n, errors))
        return 1

    # write output NDJSON atomically and write log
    try:
        write_atomic(out_name, "\n".join(out_lines) + "\n")
    except Exception as e:
        errors.append(f"[FATAL] Error writing {out_name}: {e}")
        append_log(log_name, header_log(n, errors))
        return 1

    #prepare final log content
    summary = [
        f"Run {n} processed: lines_read={processed_lines}, lines_written={written_lines}",
        f"Output: {out_name}",
    ]
    log_lines = header_log(n, errors) + summary
    append_log(log_name, log_lines)
    return 0


def header_log(run_number: int, errors: List[str]) -> List[str]:
    header = [
        f"term_run{run_number} errors",
        f"timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "-" * 40,
    ]
    if errors:
        header += ["Errors:"] + errors + ["-" * 40]
    else:
        header += ["No errors detected", "-" * 40]
    return header


def main() -> int:
    try:
        ballistics = load_ballistics_runs("ballistics_runs.json")
    except Exception as e:
        msg = f"[FATAL] Unable to read ballistics_runs.json: {e}"
        print(msg)
        write_atomic("term_run_all_errors.log", msg + "\n")
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
            stale_log = f"term_run{n}_errors.log"
            for p in (stale_out, stale_log):
                try:
                    if os.path.isfile(p):
                        os.remove(p)
                        print(f"[CLEANUP] removed stale file: {p}")
                except Exception as e:
                    print(f"[WARN] failed to remove {p}: {e}")

    found = find_trac_files()
    if not found:
        print("No trac_runN.json files found (N=1..3). Nothing to do.")
        return 0

    exit_code = 0
    for n in found:
        if n not in declared_runs:
            #skip stale trac files that don't match current ballistics_runs.json
            log_name = f"term_run{n}_errors.log"
            msg_lines = header_log(n, [f"[SKIP] trac_run{n}.json exists but no matching run_number in ballistics_runs.json; skipping."])
            append_log(log_name, msg_lines)
            print(f"[SKIP] trac_run{n}.json found but no matching run_number in ballistics_runs.json; skipped.")
            continue

        rc = process_trac_run(n, ballistics)
        if rc != 0:
            exit_code = rc  #return non-zero if any run had fatal issue

    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
