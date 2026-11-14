#!/usr/bin/env python3
"""
Forge Neo (sd-webui-forge-classic: neo branch) Launcher for Google Colab
Optimized for Tesla T4 GPU
Repo: https://github.com/Haoming02/sd-webui-forge-classic.git (branch: neo)
"""

import os
import sys
import subprocess
import shutil
import time
import argparse
from pathlib import Path

# Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"{CYAN}{BOLD}")
    print("=" * 60)
    print("      🚀 FORGE NEO LAUNCHER - GOOGLE COLAB (T4 GPU)")
    print("=" * 60)
    print(f"{RESET}")

def check_environment():
    print(f"{BOLD}[1/5] Memeriksa Lingkungan GPU & Sistem...{RESET}")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            print(f"{GREEN}✓ GPU Terdeteksi: {device_name} ({vram_gb:.2f} GB VRAM){RESET}")
            if "T4" in device_name:
                print(f"{GREEN}✓ Target GPU Tesla T4 cocok. Optimalisasi VRAM akan diterapkan.{RESET}")
        else:
            print(f"{RED}⚠️ Peringatan: GPU tidak terdeteksi!{RESET}")
            print(f"{YELLOW}Pastikan Anda mengubah jenis runtime di Google Colab:{RESET}")
            print(f"{YELLOW}  Runtime -> Change runtime type -> T4 GPU{RESET}")
    except ImportError:
        print(f"{YELLOW}PyTorch belum terdeteksi. Colab akan menggunakan PyTorch default.{RESET}")

def setup_directories(base_path):
    print(f"\n{BOLD}[2/5] Menyiapkan Direktori & Integrasi Google Drive...{RESET}")
    drive_mounted = os.path.exists("/content/drive/MyDrive")
    if drive_mounted:
        print(f"{GREEN}✓ Google Drive terdeteksi (/content/drive/MyDrive).{RESET}")
        drive_outputs = Path("/content/drive/MyDrive/Forge_Outputs")
        drive_outputs.mkdir(parents=True, exist_ok=True)
        
        # Symlink outputs ke Drive agar hasil render aman
        local_outputs = base_path / "outputs"
        if not local_outputs.exists():
            local_outputs.symlink_to(drive_outputs)
            print(f"{GREEN}✓ Output disinkronkan ke Google Drive: {drive_outputs}{RESET}")
    else:
        print(f"{YELLOW}ℹ Google Drive tidak dimount. Hasil render akan tersimpan lokal di {base_path / 'outputs'}{RESET}")
        print(f"{YELLOW}  (Tip: Jalankan `from google.colab import drive; drive.mount('/content/drive')` jika ingin menyimpan hasil ke Drive).{RESET}")

def clone_forge_neo(target_dir):
    print(f"\n{BOLD}[3/5] Mengunduh / Memperbarui Forge Neo (Branch: neo)...{RESET}")
    repo_url = "https://github.com/Haoming02/sd-webui-forge-classic.git"
    
    if not target_dir.exists():
        print(f"Mengkloning Forge Neo ke {target_dir}...")
        cmd = ["git", "clone", "-b", "neo", "--depth", "1", repo_url, str(target_dir)]
        subprocess.run(cmd, check=True)
        print(f"{GREEN}✓ Berhasil mengkloning Forge Neo!{RESET}")
    else:
        print(f"Direktori {target_dir} sudah ada. Memperbarui branch neo...")
        subprocess.run(["git", "-C", str(target_dir), "pull"], check=False)
        print(f"{GREEN}✓ Forge Neo sudah yang terbaru.{RESET}")

def install_dependencies():
    print(f"\n{BOLD}[4/5] Memastikan Paket uv & Dependensi...{RESET}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)
        print(f"{GREEN}✓ `uv` siap digunakan untuk instalasi dependensi super cepat.{RESET}")
    except Exception as e:
        print(f"{YELLOW}Gagal menginstall uv ({e}), akan menggunakan pip standar.{RESET}")

def download_file(url, destination_path, desc="File"):
    if not url:
        return
    print(f"Mengunduh {desc} dari {url}...")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-L", "-o", str(destination_path), url]
    subprocess.run(cmd, check=True)
    print(f"{GREEN}✓ Selesai mengunduh {desc}: {destination_path.name}{RESET}")

def launch_webui(forge_dir, extra_args):
    print(f"\n{BOLD}[5/5] Menjalankan Forge Neo WebUI...{RESET}")
    
    # Argumen default untuk Google Colab T4
    launch_args = [
        sys.executable,
        "launch.py",
        "--share",                           # Wajib untuk tunnel publik gradio.live di Colab
        "--enable-insecure-extension-access", # Mengizinkan install extensions via WebUI
        "--theme", "dark",                   # Tampilan tema gelap
        "--cuda-stream",                     # Optimalisasi stream CUDA
        "--pin-shared-memory"                # Kecepatan swap memori
    ]
    
    if extra_args:
        launch_args.extend(extra_args)
        
    print(f"Menjalankan perintah:")
    print(f"{CYAN}{' '.join(launch_args)}{RESET}\n")
    print(f"{YELLOW}👉 Perhatikan output di bawah. Tunggu link publik `https://xxxxxxxx.gradio.live` muncul.{RESET}")
    print(f"{YELLOW}👉 Buka link tersebut di browser untuk mengakses WebUI Forge Neo.{RESET}\n")
    
    os.chdir(forge_dir)
    subprocess.run(launch_args)

def main():
    parser = argparse.ArgumentParser(description="Forge Neo Launcher untuk Colab T4 GPU")
    parser.add_argument("--dir", default="/content/forge-neo" if os.path.exists("/content") else "./forge-neo", 
                        help="Lokasi instalasi Forge Neo")
    parser.add_argument("--model-url", default=None, 
                        help="URL langsung ke file model (.safetensors) untuk diunduh otomatis")
    parser.add_argument("--starter-model", action="store_true",
                        help="Unduh model starter (DreamShaper 8 SD1.5) jika belum ada model")
    args, unknown = parser.parse_known_args()

    banner()
    check_environment()
    
    forge_path = Path(args.dir).resolve()
    clone_forge_neo(forge_path)
    setup_directories(forge_path)
    install_dependencies()

    # Cek & Unduh Model jika diminta
    models_dir = forge_path / "models" / "Stable-diffusion"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    if args.model_url:
        filename = args.model_url.split("/")[-1].split("?")[0] or "custom_model.safetensors"
        if not filename.endswith(".safetensors") and not filename.endswith(".ckpt"):
            filename += ".safetensors"
        download_file(args.model_url, models_dir / filename, desc="Model Checkpoint")
    elif args.starter_model:
        existing = list(models_dir.glob("*.safetensors")) + list(models_dir.glob("*.ckpt"))
        if not existing:
            starter_url = "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
            download_file(starter_url, models_dir / "DreamShaper_8_pruned.safetensors", desc="Starter Model (DreamShaper 8)")
        else:
            print(f"{GREEN}✓ Model sudah ada di direktori: {[f.name for f in existing]}{RESET}")

    launch_webui(forge_path, unknown)

if __name__ == "__main__":
    main()
