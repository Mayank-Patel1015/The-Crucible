import subprocess
import re

def sample_hardware_power(duration_seconds=45):
    """Samples Apple Silicon CPU+GPU power. Requires sudo for powermetrics."""
    cmd = ["sudo", "powermetrics", "-i", "1000", "-n", str(int(duration_seconds)), "-s", "cpu_power"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, _ = process.communicate()
    
    mw_readings = re.findall(r"Combined Power \(CPU \+ GPU\): (\d+) mW", stdout)
    if not mw_readings:
        mw_readings = re.findall(r"CPU Power: (\d+) mW", stdout)
    
    if mw_readings:
        avg_mw = sum(map(int, mw_readings)) / len(mw_readings)
        joules = (avg_mw / 1000.0) * duration_seconds
        return joules, avg_mw / 1000.0
    return 0.0, 0.0
