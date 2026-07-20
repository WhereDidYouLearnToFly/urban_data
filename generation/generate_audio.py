#!/usr/bin/env python3
"""Generate audio assets: Gemma rewrite (via ComfyUI API) -> VibeVoice TTS
(standalone, bypassing ComfyUI due to a transformers version conflict between
ComfyUI core and VibeVoice-ComfyUI) -> ffmpeg radio-degradation filter.

Driven by generation/manifest_audio.json. Must be run with the isolated
vibevoice-env interpreter:
    ~/ComfyUI/vibevoice-env/bin/python3 generation/generate_audio.py
"""
import json
import time
import subprocess
import sys
import os
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

import numpy as np
import torch
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest_audio.json"
COMFYUI_URL = "http://127.0.0.1:8188"

VVEMBED = os.path.expanduser("~/ComfyUI/custom_nodes/VibeVoice-ComfyUI/vvembed")
sys.path.insert(0, VVEMBED)
from modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference  # noqa: E402
from processor.vibevoice_processor import VibeVoiceProcessor  # noqa: E402

MODEL_PATH = os.path.expanduser("~/ComfyUI/models/vibevoice/VibeVoice-1.5B")
TOKENIZER_PATH = os.path.expanduser("~/ComfyUI/models/vibevoice/tokenizer")

REWRITE_INSTRUCTION = (
    "The following is an incident-report log line describing a radio or phone transmission. "
    "Rewrite it as the exact spoken words a person would actually say over the radio/phone. "
    "If it contains a quoted statement, use only that statement, rephrased naturally in first "
    "person if needed. Do NOT include labels like 'Ham radio report:' or 'Citizen phone report:', "
    "do not describe the speaker's role, do not include quote marks. Keep it short and urgent, "
    "like real radio chatter. Output ONLY the spoken words, nothing else.\n\nLog line: {desc}"
)


def submit(workflow: dict) -> dict:
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("HTTP error body:", e.read().decode())
        raise


def wait_for(prompt_id: str, timeout: int = 120) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}")
        hist = json.loads(req.read())
        if prompt_id in hist:
            return hist[prompt_id]
        time.sleep(1)
    raise TimeoutError(f"prompt {prompt_id} timed out")


def seed_for(event_id: str, scenario: str) -> int:
    h = hashlib.sha256(f"{scenario}:{event_id}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def rewrite_text(description: str) -> str:
    workflow = {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "gemma_3_12B_it_fp4_mixed.safetensors", "type": "ltxv", "device": "default"}},
        "2": {"class_type": "TextGenerate", "inputs": {
            "clip": ["1", 0],
            "prompt": REWRITE_INSTRUCTION.format(desc=description),
            "max_length": 150,
            "sampling_mode": "off",
        }},
        "3": {"class_type": "SaveText", "inputs": {"text": ["2", 0], "filename": "tmp/audio_rewrite"}},
    }
    res = submit(workflow)
    hist = wait_for(res["prompt_id"])
    return hist["outputs"]["3"]["text"][0]


def create_synthetic_voice_sample(speaker_idx: int = 0) -> np.ndarray:
    sample_rate = 24000
    duration = 1.0
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    base_frequencies = [120, 180, 140, 200]
    base_freq = base_frequencies[speaker_idx % len(base_frequencies)]
    formant1 = 800 + speaker_idx * 100
    formant2 = 1200 + speaker_idx * 150
    voice_sample = (
        0.6 * np.sin(2 * np.pi * base_freq * t)
        + 0.25 * np.sin(2 * np.pi * base_freq * 2 * t)
        + 0.15 * np.sin(2 * np.pi * base_freq * 3 * t)
        + 0.1 * np.sin(2 * np.pi * formant1 * t) * np.exp(-t * 2)
        + 0.05 * np.sin(2 * np.pi * formant2 * t) * np.exp(-t * 3)
        + 0.02 * np.random.normal(0, 1, len(t))
    )
    vibrato_freq = 4 + speaker_idx * 0.3
    envelope = np.exp(-t * 0.3) * (1 + 0.1 * np.sin(2 * np.pi * vibrato_freq * t))
    voice_sample *= envelope * 0.08
    return voice_sample.astype(np.float32)


def generate_tts(model, processor, text: str, seed: int) -> np.ndarray:
    formatted_text = f"Speaker 1: {text}"
    voice_samples = [create_synthetic_voice_sample(0)]

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    model.set_ddpm_inference_steps(20)

    inputs = processor([formatted_text], voice_samples=[voice_samples], return_tensors="pt", return_attention_mask=True)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(**inputs, tokenizer=processor.tokenizer, cfg_scale=1.3, max_new_tokens=None, do_sample=False)

    speech_tensors = output.speech_outputs
    audio_tensor = torch.cat(speech_tensors, dim=-1) if isinstance(speech_tensors, list) else speech_tensors
    return audio_tensor.cpu().float().numpy().squeeze()


def apply_radio_filter(raw_path: Path, out_path: Path):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(raw_path)],
        capture_output=True, text=True, check=True,
    )
    duration = probe.stdout.strip()
    filt = (
        "[0:a]highpass=f=500,lowpass=f=2800,acompressor=threshold=-18dB:ratio=8:attack=5:release=50,volume=3[voice];"
        f"anoisesrc=color=white:amplitude=0.04:duration={duration}[noise];"
        "[voice][noise]amix=inputs=2:duration=first:weights=1 0.5[out]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_path), "-filter_complex", filt, "-map", "[out]", "-ar", "24000", str(out_path)],
        capture_output=True, check=True,
    )


def main():
    entries = json.loads(MANIFEST_PATH.read_text())
    print(f"{len(entries)} audio entries to generate")

    print("Loading VibeVoice model...")
    t0 = time.time()
    model = VibeVoiceForConditionalGenerationInference.from_pretrained(
        MODEL_PATH, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="cuda", local_files_only=True,
    )
    processor = VibeVoiceProcessor.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True, language_model_pretrained_name=TOKENIZER_PATH,
    )
    print(f"Model loaded in {time.time()-t0:.1f}s")

    tmp_raw = REPO_ROOT / "generation" / "_tmp_audio_raw.wav"

    for i, entry in enumerate(entries):
        target = REPO_ROOT / entry["target_path"]
        if target.exists():
            print(f"  [{i+1}/{len(entries)}] {entry['event_id']} already exists, skipping")
            continue

        print(f"  [{i+1}/{len(entries)}] {entry['scenario']}/{entry['event_id']}: rewriting...")
        try:
            spoken_text = rewrite_text(entry["description"])
        except Exception as e:
            print(f"    FAILED rewrite: {e}")
            continue

        seed = seed_for(entry["event_id"], entry["scenario"])
        try:
            audio_np = generate_tts(model, processor, spoken_text, seed)
        except Exception as e:
            print(f"    FAILED tts: {e}")
            continue

        sf.write(tmp_raw, audio_np, 24000)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            apply_radio_filter(tmp_raw, target)
        except subprocess.CalledProcessError as e:
            print(f"    FAILED filter: {e.stderr.decode()[:300]}")
            continue

        print(f"    saved -> {entry['target_path']}")

    if tmp_raw.exists():
        tmp_raw.unlink()
    print("done")


if __name__ == "__main__":
    main()
