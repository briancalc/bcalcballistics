#holdover.py
class holdover:
    def __init__(self, yards, moa_correction, impact_in, path_inches, seconds,
                 wind_moa_correction=0, wind_drift_inches=0):
        self.yards = yards
        self.moa_correction = moa_correction
        self.impact_in = impact_in
        self.path_inches = path_inches
        self.seconds = seconds
        self.wind_moa_correction = wind_moa_correction
        self.wind_drift_inches = wind_drift_inches

    def get_yards(self):
        return self.yards

    def get_moa_correction(self):
        return self.moa_correction

    def get_wind_moa_correction(self):
        return self.wind_moa_correction

    def get_wind_drift_inches(self):
        return self.wind_drift_inches

