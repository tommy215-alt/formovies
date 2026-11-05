"""Resemble Enhance（MIT、ResembleAI）で声を「スタジオで録った声」に作り直す、常駐の小さなプロセス。
収録スタジオ（narration_studio.py）が専用の環境の Python で起動し、1 行ずつ JSON で頼む：
    {"in": "edit/L06.wav", "out": "ai/L06.wav"}  →  {"ok": true, "sec": 1.2} または {"ok": false, "error": "..."}

専用の環境：%LOCALAPPDATA%\\reverse_tools\\enhance（torch 2.5.1＋CUDA 12.1、resemble-enhance 0.0.1 を依存なしで）。
resemble-enhance は学習用の deepspeed（Windows に入らない）を読み込むので、推論に要らない部分だけの代わりをここで置く。
モデルは Hugging Face の ResembleAI/resemble-enhance（enhancer_stage2）を %LOCALAPPDATA%\\reverse_tools\\enhance_model に。
"""
import json
import os
import sys
import time
import types
from pathlib import Path

MODEL_DIR = Path(os.environ["LOCALAPPDATA"]) / "reverse_tools" / "enhance_model"


def stub_deepspeed():
    """deepspeed の代わり（推論では呼ばれない。読み込みを通すだけ）"""
    ds = types.ModuleType("deepspeed")
    acc = types.ModuleType("deepspeed.accelerator")
    rt = types.ModuleType("deepspeed.runtime")
    eng = types.ModuleType("deepspeed.runtime.engine")
    ut = types.ModuleType("deepspeed.runtime.utils")
    ds.DeepSpeedConfig = type("DeepSpeedConfig", (), {"__init__": lambda self, *a, **k: None})
    ds.init_distributed = lambda *a, **k: None
    acc.get_accelerator = lambda: types.SimpleNamespace(communication_backend_name=lambda: "gloo")
    eng.DeepSpeedEngine = type("DeepSpeedEngine", (), {})
    ut.clip_grad_norm_ = lambda *a, **k: 0.0
    ds.accelerator, ds.runtime, rt.engine, rt.utils = acc, rt, eng, ut
    for name, m in (("deepspeed", ds), ("deepspeed.accelerator", acc), ("deepspeed.runtime", rt),
                    ("deepspeed.runtime.engine", eng), ("deepspeed.runtime.utils", ut)):
        sys.modules[name] = m


def model_dir():
    run = MODEL_DIR / "enhancer_stage2"
    if not (run / "ds" / "G" / "default" / "mp_rank_00_model_states.pt").exists():
        from huggingface_hub import snapshot_download
        snapshot_download("ResembleAI/resemble-enhance", local_dir=str(MODEL_DIR),
                          allow_patterns=["enhancer_stage2/*", "enhancer_stage2/**"])
    return run


def main():
    stub_deepspeed()
    if os.name == "nt":                     # モデルの保存ファイルに Linux のパスの型が入っている（Windows で読めるように）
        import pathlib
        pathlib.PosixPath = pathlib.WindowsPath
    import torch
    import torchaudio
    from resemble_enhance.enhancer.inference import enhance
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    run = model_dir()
    print(json.dumps({"ready": True, "device": dev}), flush=True)
    for line in sys.stdin:
        try:
            job = json.loads(line.lstrip("﻿"))
            t = time.time()
            wav, sr = torchaudio.load(job["in"])
            wav = wav.mean(0)
            # lambd：雑音・反響を取る強さ（0〜1）、tau：作り直しの自由さ（大きいほど声が変わりやすい）、nfe：計算の細かさ
            out, osr = enhance(wav, sr, dev, nfe=job.get("nfe", 64), solver="midpoint",
                               lambd=job.get("lambd", 0.9), tau=job.get("tau", 0.5), run_dir=run)
            torchaudio.save(job["out"], out.unsqueeze(0).cpu(), osr)
            print(json.dumps({"ok": True, "sec": round(time.time() - t, 2)}), flush=True)
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"[:400]}), flush=True)


if __name__ == "__main__":
    main()
