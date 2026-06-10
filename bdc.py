# bdc.py ballistic drop compensation for given range
import atmosphere
import angles
import ballistics
import dataholder2
import os


# revised
def get_run_data(run_index: int = 0) -> dict:
    runs = dataholder2.get_runs()

    if not runs:
        raise IndexError("No runs available in dataholder2. Please enter data via the GUI first.")

    if run_index >= len(runs) or run_index < 0:
        raise IndexError(
            f"Run index {run_index} out of range. Available runs: {len(runs)}"
        )

    run = runs[run_index]

    required_keys = [
        'bc', 'v', 'sight_height', 'shooting_angle', 'zero_range',
        'windspeed', 'windangle', 'altitude', 'barometer',
        'temperature', 'relative_humidity', 'drag_function'
    ]

    missing_keys = [key for key in required_keys if key not in run]
    if missing_keys:
        raise ValueError(f"Run data missing required keys: {missing_keys}")

    return run


def calcBDC(range_yards: int, run_index: int = 0) -> list:

    try:
        run_data = get_run_data(run_index)
    except (IndexError, ValueError) as e:
        print(f"Error loading run data: {e}")
        raise

    bc = run_data['bc']
    v = run_data['v']
    sight_height = run_data['sight_height']
    shooting_angle = run_data['shooting_angle']
    zero_range = run_data['zero_range']
    windspeed = run_data['windspeed']
    windangle = run_data['windangle']
    altitude = run_data['altitude']
    barometer = run_data['barometer']
    temperature = run_data['temperature']
    relative_humidity = run_data['relative_humidity']
    drag_function = run_data['drag_function']

    if relative_humidity > 1.0:
        relative_humidity = relative_humidity / 100.0

    bc_corrected = atmosphere.atmosphere_correction(
        bc, altitude, barometer, temperature, relative_humidity
    )

    print(
        f"Run {run_data.get('run_number', 'Unknown')}: "
        f"Cartridge={run_data.get('cartridge', 'Unknown')}: "
        f"Caliber={run_data.get('caliber', 'Unknown')}: "
        f"Grains={run_data.get('weight', 'Unknown')}: "
        f"Drag Function={run_data.get('drag_function', 'Unknown')}: "
        f"BC={run_data.get('bc', 'Unknown')}: "
        f"Velocity={run_data.get('v', 'Unknown')}: "
        f"Shooting Angle={run_data.get('shooting_angle', 'Unknown')}: "
        f"Zero Range={run_data.get('zero_range', 'Unknown')}"
    )

    #print(f"  Corrected BC: {bc_corrected}") #for debugging

    zeroangle = angles.zero_angle(
        drag_function, bc_corrected, v,
        sight_height, zero_range, 0,
        shooting_angle
    )

    with open("debug_output.txt", "a") as f:
        f.write(
            f"\nbdc.py FINAL: shooting_angle={shooting_angle}, "
            f"calculated zero_angle={zeroangle}\n"
        )

    hold_overs = ballistics.solve(
        drag_function, bc_corrected, v, sight_height, shooting_angle,
        zeroangle, windspeed, windangle,
        altitude, barometer, temperature,
        relative_humidity
    )


    # file routing
    source_file = "trac_flat.json"
    target_file = f"trac_run{run_index + 1}.json"

    if os.path.exists(source_file):
        if os.path.exists(target_file):
            os.remove(target_file)

        os.rename(source_file, target_file)
    else:
        print(f"Warning: {source_file} not found for run {run_index + 1}")

    return hold_overs


def calcBDC_all_runs(range_yards: int) -> list:

    runs = dataholder2.get_runs()

    if not runs:
        raise IndexError("No runs available in dataholder2.")

    results = []
    for i in range(len(runs)):
        try:
            result = calcBDC(range_yards, run_index=i)
            results.append(result)
        except (IndexError, ValueError) as e:
            print(f"Error calculating BDC for run {i}: {e}")
            results.append(None)

    return results
