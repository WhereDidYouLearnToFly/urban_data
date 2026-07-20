#!/usr/bin/env python3
"""Generate photo assets via ComfyUI: Gemma prompt-rewrite -> flux1-krea-dev.

Driven by generation/manifest.json (type == "photo"). Submits one combined
ComfyUI API workflow per event (rewrite + generation in a single graph),
polls /history, copies the result to the manifest's target_path.
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

REWRITE_INSTRUCTION = (
    "Rewrite the following incident-report sensor description as a single vivid, "
    "well-formed prompt for a photorealistic photojournalism-style image generator. "
    "Keep the location and key visual facts. Output ONLY the rewritten prompt text, "
    "nothing else, no preamble.\n\nDescription: {desc}"
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


def wait_for(prompt_id: str, timeout: int = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}")
        hist = json.loads(req.read())
        if prompt_id in hist:
            return hist[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"prompt {prompt_id} timed out")


def seed_for(event_id: str, scenario: str) -> int:
    h = hashlib.sha256(f"{scenario}:{event_id}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def build_workflow(description: str, filename_prefix: str, seed: int) -> dict:
    return {
        "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "gemma_3_12B_it_fp4_mixed.safetensors", "type": "ltxv", "device": "default"}},
        "2": {"class_type": "TextGenerate", "inputs": {
            "clip": ["1", 0],
            "prompt": REWRITE_INSTRUCTION.format(desc=description),
            "max_length": 200,
            "sampling_mode": "off",
        }},
        "3": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-krea-dev_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "4": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp16.safetensors", "type": "flux", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": ["2", 0]}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["3", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
            "seed": seed, "steps": 20, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1,
        }},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["9", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": filename_prefix}},
    }


def main():
    entries = [e for e in json.loads(MANIFEST_PATH.read_text()) if e["type"] == "photo"]
    print(f"{len(entries)} photo entries to generate")

    for i, entry in enumerate(entries):
        target = REPO_ROOT / entry["target_path"]
        if target.exists():
            print(f"  [{i+1}/{len(entries)}] {entry['event_id']} already exists, skipping")
            continue

        prefix = f"gen_{entry['scenario']}_{entry['event_id']}"
        seed = seed_for(entry["event_id"], entry["scenario"])
        workflow = build_workflow(entry["description"], prefix, seed)

        print(f"  [{i+1}/{len(entries)}] {entry['scenario']}/{entry['event_id']}: submitting...")
        res = submit(workflow)
        pid = res["prompt_id"]
        hist = wait_for(pid)

        if hist.get("status", {}).get("status_str") != "success":
            print(f"    FAILED: {json.dumps(hist.get('status', {}))}")
            continue

        images = hist.get("outputs", {}).get("11", {}).get("images", [])
        if not images:
            print("    FAILED: no image output")
            continue

        src = COMFYUI_OUTPUT_DIR / images[0]["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, target)
        print(f"    saved -> {entry['target_path']}")

    print("done")


if __name__ == "__main__":
    main()
