# utils.py
import math


def moaToMil(moa):
    """ Convert MOA to milliradians.
         Inputs: moa = angle in minutes
         Returns: angle in milliradians
    """
    return moa * 0.290888208859


def milToInch(mil, feet):
    """ Convert milliradians to inches.
         Inputs: mil = angle in milliradians, feet = adjacent side in feet
         Returns: opposite side in inches
    """
    return (feet * 12) * (mil / 1000)


def moaToInch(moa, feet):
    """ Convert MOA to inches using milliradians as intermediate step.
         Inputs: moa = angle in minutes, feet = adjacent side in feet
         Returns: opposite side in inches
    """
    mil = moaToMil(moa)
    return milToInch(mil, feet)
