#ballistics.py

import windage
from config import GRAVITY, BALLISTICS_COMPUTATION_MAX_YARDS, OUTPUT_RANGES
import angles
import atmosphere
import math
import drag
import utils
import json


def solve(drag_function, drag_coefficient, vi, sight_height, shooting_angle, zero_angle, wind_speed, wind_angle,
          altitude, barometer, temperature, relative_humidity):

    # Adjusts drag coefficient for non-standard temperature, pressure, altitude, and humidity
    corrected_drag_coeff = atmosphere.atmosphere_correction(
        drag_coefficient,
        altitude,
        barometer,
        temperature,
        relative_humidity
    )

    t = 0       #time per dt step
    dt = 0    #step interval
    v = 0     #velocity calculated using vx and vy
    vx = 0     #horizontal velocity
    vx1 = 0   #becomes previous vx velocity (used to compute average horizontal position along with vx)
    vy = 0     #vertical velocity
    vy1 = 0   #becomes previous vy velocity (used to compute average vertical position along with vy)
    dv = 0     #impact of drag and wind and (to be confirmed) atmospheric conditions
    dvx = 0
    dvy = 0
    x = 0
    y = 0

    hwind = windage.headwind(wind_speed, wind_angle)
    cwind = windage.crosswind(wind_speed, wind_angle)


    gx = 0 #Gravity always acts vertically, not relative to bore angle
    gy = GRAVITY

    theta = angles.deg_to_rad(zero_angle)
    #corrected_drag_coeff is the corrected (by drag.py) bc coefficient.  this is called just drag_coefficient in the angles.py file

    vx = vi * math.cos(theta)
    vy = vi * math.sin(theta)

    y = -sight_height/12 #convert sight_height inches into feet for rest of calculations
    n = 0

    # Removed: hold_overs = points()

    # Prepare results list for 1..800 (index 0 -> range 1)
    MAX_YARDS = 800
    results = [None] * MAX_YARDS

    while True:
        vx1 = vx
        vy1 = vy
        v = math.sqrt(vx*vx + vy*vy) #basically a^2 + b^2 = c^2 where v=c, vx=x, vy= is b (vertical)
        #dt = 0.3/v
        dt = .0001
        # Compute acceleration using the drag function retardation with atmospheric corrections
        dv = drag.retard(drag_function, corrected_drag_coeff, v+hwind)
        dvx = -(vx/v)*dv
        dvy = -(vy/v)*dv

        # Compute velocity, including the resolved gravity vectors.
        vx = vx + dt*dvx #dt*gx is 0 as gx is always 0
        vy = vy + dt*dvy + dt*gy

        if x/3 >= n:
            if x > 0:
                #run until line of sight distance = total 800 yards
                range_yards = round(x / math.cos(math.radians(shooting_angle))/3)

                # Account for shooting angle - measure drop relative to sight line
                #when shooting_angle = 0 then radians(shooting_angle) =0 so sight_line_height = 0
                #sight_line_height is the veritcal derived from the x distance tanget of shooting angle
                #sight_line_height is as if laser shot from sight with no gravity, drag, wind, etc
                #y is the bullet path estimated by the calculator so the difference is the bullet drop
                #sight_line_height = x * math.tan(math.radians(shooting_angle))
                #drop_relative_to_sight = y - sight_line_height
                #replaced the 2 lines above with the 3 lines below
                theta_los = math.radians(shooting_angle)
                sight_line_height = ( x * math.tan(theta_los))
                drop_relative_to_sight = (y - sight_line_height) * math.cos(theta_los)

                # Vertical correction relative to sight line
                moa_correction = -angles.rad_to_moa(math.atan(drop_relative_to_sight / x))
                path_inches = drop_relative_to_sight * 12
                 #wind_drift_inches = windage.windage(cwind, vi, x, t) #old code - trying something with next 2 lines
                vx_windcomponent = vi * math.cos(math.radians(zero_angle))
                wind_drift_inches = windage.windage(cwind, vx_windcomponent, x, t)

                wind_moa_correction = angles.rad_to_moa(math.atan(wind_drift_inches / 12 / x))
                seconds = t+dt

                # Only print to terminal if range yards is in predefined ranges
                if range_yards in OUTPUT_RANGES:
                    print("range yards {}".format(range_yards))
                    #print("shooting_angle {}".format(round(shooting_angle, 0)))
                    print("drop (in) {}".format(round(path_inches, 2)))
                    print("wind drift (in) {}".format(round(wind_drift_inches, 2)))
                    print("moa correction {}".format(round(moa_correction, 2)))
                    print("wind moa correction {}".format(round(wind_moa_correction, 2)))
                    print("velocity (ft/s) {}".format(round(v, 0)))
                    print("TOF seconds {}".format(round(seconds, 3)))

                # Removed: hold_overs.add_point(holdover(...)) block

                # If in 1..800, store a dict matching printed fields
                if 1 <= range_yards <= MAX_YARDS:
                    results[range_yards - 1] = {
                        "range_yards": range_yards,
                        "velocity_ft_s": round(v, 0),
                        "drop_in": round(path_inches, 2),
                        "wind_drift_in": round(wind_drift_inches, 2),
                        "moa_correction": round(moa_correction, 2),
                        "wind_moa_correction": round(wind_moa_correction, 2),
                        "tof_seconds": round(seconds, 2)#,
                      }

            n = n + 1

        # Compute new position based on average velocity
        x = x + dt * (vx+vx1)/2
        y = y + dt * (vy+vy1)/2

        if (math.fabs(vy) > math.fabs(3*vx) or n >= BALLISTICS_COMPUTATION_MAX_YARDS):
            break

        t = t + dt

    # Ensure any None entries are explicit nulls (they already are None which serializes to null)
    # Write trac_flat.json (overwrite) in current directory
    # Write trac_flat.json as NDJSON (one JSON value per line for ranges 1..800)
    with open("trac_flat.json", "w", encoding="utf-8") as f:
        for entry in results:
            f.write(json.dumps(entry) if entry is not None else "null")
            f.write("\n")

    return None
