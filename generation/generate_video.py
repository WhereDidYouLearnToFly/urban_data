#!/usr/bin/env python3
"""Generate video assets via ComfyUI: Gemma prompt-rewrite -> ltx-2-19b.

Driven by generation/manifest.json (type == "video"). Submits one combined
ComfyUI API workflow per event, polls /history, copies the result to the
manifest's target_path.
"""
import json
import time
import shutil
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"
COMFYUI_URL = "http://127.0.0.1:8188"
COMFYUI_OUTPUT_DIR = Path.home() / "ComfyUI" / "output"


def submit(workflow: dict) -> dict:
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("HTTP error body:", e.read().decode())
        raise


def wait_for(prompt_id: str, timeout: int = 900) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}")
        hist = json.loads(req.read())
        if prompt_id in hist:
            return hist[prompt_id]
        time.sleep(3)
    raise TimeoutError(f"prompt {prompt_id} timed out")


def seed_for(event_id: str, scenario: str) -> int:
    h = hashlib.sha256(f"{scenario}:{event_id}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def build_workflow(description: str, filename_prefix: str, seed: int) -> dict:
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}},
        "2": {"class_type": "ModelSamplingLTXV", "inputs": {"model": ["1", 0], "max_shift": 2.05, "base_shift": 0.95}},
        "3": {"class_type": "LTXAVTextEncoderLoader", "inputs": {"text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors", "ckpt_name": "ltx-2-19b-dev-fp8.safetensors", "device": "default"}},
        "4": {"class_type": "TextGenerateLTX2Prompt", "inputs": {
            "clip": ["3", 0],
            "prompt": description,
            "max_length": 300,
            "sampling_mode": "off",
            "use_default_template": True,
        }},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": ["4", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": "worst quality, blurry, distorted, static, low framerate"}},
        "7": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": 24.0}},
        "8": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 768, "height": 512, "length": 49, "batch_size": 1}},
        "9": {"class_type": "KSampler", "inputs": {
            "model": ["2", 0], "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["8", 0],
            "seed": seed, "steps": 20, "cfg": 3.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        }},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
        "11": {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "fps": 24.0}},
        "12": {"class_type": "SaveVideo", "inputs": {"video": ["11", 0], "filename_prefix": filename_prefix, "format": "auto", "codec": "auto"}},
    }


def main():
    entries = [e for e in json.loads(MANIFEST_PATH.read_text()) if e["type"] == "video"]
    print(f"{len(entries)} video entries to generate")

    for i, entry in enumerate(entries):
        target = REPO_ROOT / entry["target_path"]
        marker = target.with_suffix(target.suffix + ".generated")
        if marker.exists():
            print(f"  [{i+1}/{len(entries)}] {entry['event_id']} already generated, skipping")
            continue

        prefix = f"gen_{entry['scenario']}_{entry['event_id']}"
        seed = seed_for(entry["event_id"], entry["scenario"])
        workflow = build_workflow(entry["description"], prefix, seed)

        print(f"  [{i+1}/{len(entries)}] {entry['scenario']}/{entry['event_id']}: submitting...")
        t0 = time.time()
        res = submit(workflow)
        pid = res["prompt_id"]
        hist = wait_for(pid)

        if hist.get("status", {}).get("status_str") != "success":
            print(f"    FAILED: {json.dumps(hist.get('status', {}))}")
            continue

        videos = hist.get("outputs", {}).get("12", {}).get("images", [])
        if not videos:
            print("    FAILED: no video output")
            continue

        src = COMFYUI_OUTPUT_DIR / videos[0]["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, target)
        marker.touch()
        print(f"    saved -> {entry['target_path']} ({time.time()-t0:.0f}s)")

    print("done")


if __name__ == "__main__":
    main()
