#example.py
""""
from bdc import calcBDC
from utils import get_incline_compensation
from utils import get_cant_compensation
import math

hold_overs = calcBDC(800)

for point in hold_overs.points:
    incline_compensation = get_incline_compensation(point.path_inches, -15)
    cant_compensation = get_cant_compensation(point.seconds, 90, 1.5)
#not printing the hold_over data as no longer required
    #print("hold_over %s %s %s %s %s" %
        #(point.yards, point.path_inches, incline_compensation, abs(point.path_inches-incline_compensation), cant_compensation))
"""

from bdc import calcBDC
import dataholder2


def main():

    runs = dataholder2.get_runs()

    if not runs:
        print("No runs available.")
        return

    for i, run in enumerate(runs):

        print("\n" + "=" * 50)
        print(f"RUN {i + 1}")
        print("=" * 50)

        hold_overs = calcBDC(800, run_index=i)


if __name__ == "__main__":
    main()
