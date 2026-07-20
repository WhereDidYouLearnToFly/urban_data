#!/usr/bin/env python3
"""Synthesize fft (RF) and float_sequence (seismic) assets for 06_nuclear_war.

Driven by generation/manifest_rf_seismic.json. Pure numpy, no models/GPU needed.
Matches the array format of the real staged data for other scenarios: a flat
JSON list of floats, 1024 points for fft (RF power spectrum), 18001 points for
float_sequence (seismic waveform).
"""
import json
import hashlib
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest_rf_seismic.json"

RF_LEN = 1024
SEISMIC_LEN = 18001
SEISMIC_SAMPLE_RATE = 100  # Hz, matches PNSN-style traces used elsewhere


def seed_for(event_id: str, scenario: str) -> int:
    h = hashlib.sha256(f"{scenario}:{event_id}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def synth_fft(level: int, description: str, rng: np.random.Generator) -> list:
    """RF power spectrum: noise floor + launch/boost-phase harmonic peaks."""
    noise_floor = rng.uniform(10, 120, RF_LEN)
    spectrum = noise_floor.copy()

    is_launch = any(k in description.lower() for k in ("launch", "boost-phase", "plume"))
    n_peaks = 4 if is_launch else 2
    base_amp = 400 + level * 150

    for _ in range(n_peaks):
        center = rng.integers(20, RF_LEN - 20)
        width = rng.uniform(3, 10)
        amp = base_amp * rng.uniform(0.6, 1.4)
        x = np.arange(RF_LEN)
        spectrum += amp * np.exp(-0.5 * ((x - center) / width) ** 2)
        # harmonic
        if is_launch and center * 2 < RF_LEN - 10:
            spectrum += (amp * 0.4) * np.exp(-0.5 * ((x - center * 2) / width) ** 2)

    spectrum = np.clip(spectrum, 5, None)
    return [round(float(v), 3) for v in spectrum]


def synth_seismic(level: int, description: str, rng: np.random.Generator) -> list:
    """Seismic waveform: ambient noise + a shock/impact transient."""
    t = np.arange(SEISMIC_LEN) / SEISMIC_SAMPLE_RATE
    ambient = rng.normal(0, 8, SEISMIC_LEN)

    is_detonation = any(k in description.lower() for k in ("detonation", "shock", "blast"))
    onset = SEISMIC_LEN * rng.uniform(0.2, 0.4)
    peak_amp = 150 + level * 60
    if is_detonation:
        peak_amp *= 1.4
        decay = 0.8
        freq = 1.2
    else:
        decay = 1.5
        freq = 0.6

    idx = np.arange(SEISMIC_LEN)
    envelope = np.where(
        idx >= onset,
        np.exp(-decay * (idx - onset) / SEISMIC_SAMPLE_RATE),
        0.0,
    )
    oscillation = np.sin(2 * np.pi * freq * (idx - onset) / SEISMIC_SAMPLE_RATE)
    transient = peak_amp * envelope * oscillation

    waveform = ambient + transient
    return [round(float(v), 5) for v in waveform]


def main():
    entries = json.loads(MANIFEST_PATH.read_text())
    print(f"{len(entries)} entries to synthesize")

    for i, entry in enumerate(entries):
        rng = np.random.default_rng(seed_for(entry["event_id"], entry["scenario"]))
        if entry["type"] == "fft":
            data = synth_fft(entry["level"], entry["description"], rng)
        elif entry["type"] == "float_sequence":
            data = synth_seismic(entry["level"], entry["description"], rng)
        else:
            raise ValueError(f"unexpected type {entry['type']}")

        target = REPO_ROOT / entry["target_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))

        if (i + 1) % 20 == 0 or i == len(entries) - 1:
            print(f"  {i + 1}/{len(entries)} done")

    print("done")


if __name__ == "__main__":
    main()
