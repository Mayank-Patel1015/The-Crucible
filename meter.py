"""
meter.py — Hardware power sampling, cross-platform.

macOS  : Apple Silicon via sudo powermetrics (accurate)
Windows: CPU utilization proxy via psutil (install: pip install psutil)
Linux  : Returns 0.0, 0.0 — skip in CI
"""

import sys
import subprocess
import re


def _sample_macos(duration_seconds: float) -> tuple[float, float]:
    """Apple Silicon CPU+GPU power via powermetrics. Requires sudo."""
    cmd = ["sudo", "powermetrics", "-i", "1000", "-n",
           str(int(duration_seconds)), "-s", "cpu_power"]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, _ = process.communicate()

    mw_readings = re.findall(r"Combined Power \(CPU \+ GPU\): (\d+) mW", stdout)
    if not mw_readings:
        mw_readings = re.findall(r"CPU Power: (\d+) mW", stdout)

    if mw_readings:
        avg_mw = sum(map(int, mw_readings)) / len(mw_readings)
        joules = (avg_mw / 1000.0) * duration_seconds
        return joules, avg_mw / 1000.0
    return 0.0, 0.0


def _sample_windows(duration_seconds: float) -> tuple[float, float]:
    """
    Windows power estimate via psutil CPU utilization.
    Assumes ~65W TDP at 100% load (reasonable for most laptops/desktops).
    Not hardware-accurate — use for relative comparison only.
    Install: pip install psutil
    """
    try:
        import psutil
        import time

        ASSUMED_TDP_WATTS = 65.0
        interval = 1.0
        samples = []
        elapsed = 0.0

        while elapsed < duration_seconds:
            pct = psutil.cpu_percent(interval=interval)
            samples.append(pct)
            elapsed += interval

        if not samples:
            return 0.0, 0.0

        avg_pct = sum(samples) / len(samples)
        avg_watts = (avg_pct / 100.0) * ASSUMED_TDP_WATTS
        joules = avg_watts * duration_seconds
        return joules, avg_watts

    except ImportError:
        print(
            "[meter] psutil not installed — run: pip install psutil\n"
            "[meter] Returning 0.0 for energy metrics.",
            file=sys.stderr,
        )
        return 0.0, 0.0


def sample_hardware_power(duration_seconds: float = 45) -> tuple[float, float]:
    """
    Returns (energy_joules, avg_watts) for the given duration.

    Platform behaviour:
      macOS   — powermetrics (accurate, requires sudo)
      Windows — psutil CPU utilization proxy (requires pip install psutil)
      Other   — returns (0.0, 0.0), logs a warning
    """
    platform = sys.platform

    if platform == "darwin":
        return _sample_macos(duration_seconds)
    elif platform == "win32":
        return _sample_windows(duration_seconds)
    else:
        # Linux CI — skip silently
        return 0.0, 0.0
