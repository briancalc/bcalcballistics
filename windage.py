#windage.py

import math
import angles


def windage(wind_speed, vi, x, t):
    """
    Calculate the lateral windage deflection for a given crosswind speed.

    The deflection is based on the difference between actual flight time (with drag)
    and vacuum flight time (no drag). This extra time exposed to crosswind causes drift.

    Physics: drift = wind_speed_ft_per_sec × (actual_flight_time - vacuum_flight_time)

    wind_speed The crosswind velocity component in mi/hr (from crosswind()).
    vi         The initial muzzle velocity of the projectile in ft/s.
    x          The range at which to calculate windage, in feet.
    t          The actual time of flight to reach range x, in seconds (computed during ballistic integration, includes drag effects).
    return The lateral windage deflection, in inches.
    raises ValueError if vi <= 0, x < 0, or t < 0.
    """

    # Input validation
    if vi <= 0:
        raise ValueError(f"Initial velocity (vi) must be positive, got {vi}")

    if x < 0:
        raise ValueError(f"Range (x) must be non-negative, got {x}")

    if t < 0:
        raise ValueError(f"Time of flight (t) must be non-negative, got {t}")

    # Edge case: zero range means zero deflection
    if x == 0:
        return 0.0

    # Convert crosswind from mi/hr to inches/second
    # 1 mi/hr = 5280 ft/mile ÷ 3600 sec/hour × 12 inches/foot = 17.6 inches/second
    vw = wind_speed * 17.6

    # Calculate vacuum flight time (no drag, straight line)
    vacuum_time = x / vi

    # Sanity check: actual time should be >= vacuum time (drag only slows projectile)
    # Allow small negative values due to floating point precision, but warn on large discrepancies
    time_difference = t - vacuum_time
    if time_difference < -0.001:  # More than 1 millisecond discrepancy
        raise ValueError(
            f"Actual flight time ({t}s) is significantly less than vacuum time ({vacuum_time}s). "
            f"This indicates invalid input: drag cannot make a projectile faster. "
            f"Check that t and x are from the same ballistic simulation."
        )

    # Wind deflection = wind speed × extra time exposed to wind
    deflection = vw * time_difference

    return deflection


def headwind(wind_speed, wind_angle):
    """
    Resolve any wind speed and angle combination into the headwind component.

    Headwind (positive) represents wind coming from ahead (opposing bullet travel).
    Tailwind (negative) represents wind from behind (assisting bullet travel).

    wind_speed  The total wind velocity in mi/hr.
    wind_angle  The angle from which the wind is coming, in degrees.
                       0°   = directly ahead (full headwind)
                       90°  = from right to left (no headwind)
                       180° = directly behind (full tailwind, negative)
                       270° or -90° = from left to right (no headwind)
    return The headwind component in mi/hr. Positive = headwind, Negative = tailwind.
    """
    w_angle = angles.deg_to_rad(wind_angle)
    return (math.cos(w_angle) * wind_speed)


def crosswind(wind_speed, wind_angle):
    """
    Resolve any wind speed and angle combination into the crosswind component.
    Crosswind represents lateral wind that pushes the projectile sideways.
    wind_speed  The total wind velocity in mi/hr.
    wind_angle  The angle from which the wind is coming, in degrees.
                       0°   = from straight ahead (no crosswind)
                       90°  = from right to left (positive, full crosswind)
                       180° = from directly behind (no crosswind)
                       270° or -90° = from left to right (negative, full crosswind)
    return            The crosswind component in mi/hr.
                       Positive = wind from right to left,
                       Negative = wind from left to right.
    """
    w_angle = angles.deg_to_rad(wind_angle)
    return (math.sin(w_angle) * wind_speed)

