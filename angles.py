# angles.py

#Find the barrel elevation angle needed so that when you fire the bullet, it will be at a specific height (target_y) when it reaches a specific distance (zero_range).
#the shooting_angle is not the final angle due to gravity, drag, wind so the actual angle needed to hit center of target is shooting_angle+-adjustment
#Angle required so the bullet intersects the sight line at 100 yd given the specific angle
import math
import drag
from config import GRAVITY

#Converts degrees to minutes of angle
def deg_to_moa(deg):
    return deg*60

#Converts degrees to radians
def deg_to_rad(deg):
    return deg*math.pi/180

#Converts minutes of angle to degr
def moa_to_deg(moa):
    return moa/60

#Converts minutes of angle to radians
def moa_to_rad(moa):
    return moa/60*math.pi/180

 #Converts radians to degree
def rad_to_deg(rad):
    return rad*180/math.pi

 #Converts radiants to minutes of angle
def rad_to_moa(rad):
    return rad*60*180/math.pi

#drag_coefficient is already the corrected drag cofficient
def zero_angle(drag_function, drag_coefficient, vi, sight_height, zero_range, y_intercept, shooting_angle):
    """
    vi - initial velocity of the projectile, in feet/s
    sight_height - height of the sighting system above the bore centerline, in inches.
    zero_range - range in yards, at which you wish the projectile to intersect y Intercept.
    y_intercept - height, in inches, you wish for the projectile to be when it crosses ZeroRange yards.
    This is usually 0 for a target zero, but could be any number.
    For example if you wish to sight your rifle in 1.5" high at 100 yds, then you would set yIntercept to 1.5, and ZeroRange to 100
    @return The angle of the bore relative to the sighting system, in degrees.
    """

    # Numerical Integration variables
    t = 0
    dt=0.0001 # Fixed small step for stability
    y = -sight_height/12
    x = 0

    # State variables for each integration loop.
    # velocity
    v = 0
    vx = 0
    vy = 0

    # Last frame's velocity, used for computing average velocity.
    vx1 = 0
    vy1 = 0

    # acceleration
    dv = 0
    dvx = 0
    dvy = 0

    # Gravitational acceleration
    Gx = 0
    Gy = GRAVITY

    # The actual angle of the bore.
    angle = 0

    # We know it's time to quit our successive approximation loop when this is 1.
    quit = 0

    # Account for shooting angle (slope)
    if shooting_angle != 0:
        slope_height = (zero_range * 3) * math.tan(math.radians(shooting_angle))
        target_y = slope_height # Fixed: Removed - sight_height/12 to match scope-relative coordinates
    else:
        target_y = y_intercept

    # The change in the bore angle used to iterate in on the correct zero angle.
    # Start with a very coarse angular change, to quickly solve even large launch angle problems.
    da = deg_to_rad(14)

    # The general idea here is to start at 0 degrees elevation, and increase the elevation by 14 degrees (converted to radians)
    # until we are above the correct elevation.  Then reduce the angular change by half, and begin reducing
    # the angle.  Once we are again below the correct angle, reduce the angular change by half again, and go
    # back up.  This allows for a fast successive approximation of the correct elevation, usually within less
    # than 20 iterations.

    while quit == 0:
        angle = da + angle


        vy = vi * math.sin(angle)
        vx = vi * math.cos(angle)

        #gravity acts only on the vertical component vy
        Gx = 0
        Gy = GRAVITY
        t = 0
        x = 0
        y = -sight_height/12

        # Initialize previous state for interpolation
        x_prev = 0
        y_prev = -sight_height/12
        vx_prev = vx
        vy_prev = vy

        target_dist = zero_range * 3
        y_at_target = 0 # Will hold the interpolated value

        while True:
            vx1 = vx
            vy1 = vy
            #hypotenuse (total velocity) = sq root (horizontal velocity ^2  + vertical velocity^2)
            v = math.pow((math.pow(vx, 2)+math.pow(vy, 2)), 0.5)

            #dv is using the data available in drag.py
            #these next few formulas are the same as found in ballistics.py just 3 expressions instead of 2 like ballistics.py
            dv = drag.retard(drag_function, drag_coefficient, v)
            dvy = -dv*vy/v*dt
            dvx = -dv*vx/v*dt

            # Update velocities
            vx = vx + dvx
            vy = vy + dvy + dt * Gy
            vx = vx + dt * Gx

            # Calculate new position
            x_new = x + dt * (vx + vx1) / 2
            y_new = y + dt * (vy + vy1) / 2

            # Check if we crossed the target distance
            if x_new >= target_dist:
                # INTERPOLATE to find exact y at x = target_dist
                # We have Point A (x, y) and Point B (x_new, y_new)
                # We want y at x = target_dist

                if (x_new - x) == 0:
                    y_at_target = y
                else:
                    fraction = (target_dist - x) / (x_new - x)
                    y_at_target = y + fraction * (y_new - y)

                # Set y to the interpolated value for the comparison logic
                y = y_at_target
                x = target_dist # Force x to be exactly target_dist
                break

            # Update state for next iteration
            x_prev = x
            y_prev = y
            vx_prev = vx
            vy_prev = vy

            x = x_new
            y = y_new

            # Break early to save CPU time if we won't find a solution.
            #if vy < 0 and y < y_intercept: tyring something new vy <-100:
            if vy < -100:
                break

            if vy > 3*vx:
                break

            t = t + dt

        # Compare the interpolated y at target_dist with target_y
        if y > target_y and da > 0:
            da = -da/2
        if y < target_y and da < 0:
            da = -da/2


        # If our accuracy is sufficient, we can stop approximating.
        if math.fabs(da) < moa_to_rad(0.001): # Tightened tolerance slightly
            quit = 1
        if angle > deg_to_rad(45):
            quit = 1

    return rad_to_deg(angle)
