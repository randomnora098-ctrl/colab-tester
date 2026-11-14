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
from urllib.parse import urlparse, unquote

# Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"{CYAN}{BOLD}")
    print("=" * 65)
    print("       🚀 FORGE NEO LAUNCHER - GOOGLE COLAB (T4 GPU)")
    print("=" * 65)
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
    print(f"\n{BOLD}[4/5] Memastikan Paket uv & Tools Download Cepat...{RESET}")
    # Install uv
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)
        print(f"{GREEN}✓ `uv` siap digunakan untuk instalasi dependensi super cepat.{RESET}")
    except Exception as e:
        print(f"{YELLOW}Gagal menginstall uv ({e}), akan menggunakan pip standar.{RESET}")

    # Install aria2 jika di Colab dan belum terinstall
    if shutil.which("aria2c") is None and os.path.exists("/usr/bin/apt-get"):
        print("Menginstall aria2 untuk download multi-threaded berkecepatan tinggi...")
        try:
            subprocess.run(["apt-get", "update", "-qq"], check=False)
            subprocess.run(["apt-get", "install", "-y", "-qq", "aria2"], check=False)
            if shutil.which("aria2c"):
                print(f"{GREEN}✓ aria2c berhasil diinstall.{RESET}")
        except Exception:
            pass

def smart_download(url, dest_file, desc="Asset"):
    """Download menggunakan aria2c (jika ada) atau curl dengan resume support."""
    dest_file = Path(dest_file)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Cek apakah file sudah ada dan ukurannya > 1MB
    if dest_file.exists() and dest_file.stat().st_size > 1024 * 1024:
        size_mb = dest_file.stat().st_size / (1024 * 1024)
        print(f"{GREEN}✓ {desc} sudah ada: {dest_file.name} ({size_mb:.1f} MB) -> Dilewati.{RESET}")
        return

    print(f"Mengunduh {desc}: {dest_file.name}...")
    print(f"URL: {url}")
    
    if shutil.which("aria2c"):
        cmd = [
            "aria2c",
            "--console-log-level=error",
            "-c", "-x", "16", "-s", "16", "-k", "1M",
            "-d", str(dest_file.parent),
            "-o", dest_file.name,
            url
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print(f"{GREEN}✓ Berhasil mengunduh {desc}: {dest_file.name}{RESET}")
            return
        else:
            print(f"{YELLOW}aria2c gagal, mencoba fallback menggunakan curl...{RESET}")

    # Fallback to curl
    cmd = ["curl", "-L", "-C", "-", "-o", str(dest_file), url]
    subprocess.run(cmd, check=True)
    print(f"{GREEN}✓ Berhasil mengunduh {desc}: {dest_file.name}{RESET}")

def parse_models_file(models_file_path, forge_path):
    """Membaca models.txt dan mengunduh asset ke folder Forge masing-masing."""
    models_file = Path(models_file_path)
    if not models_file.exists():
        return

    print(f"\n{BOLD}📂 Membaca Konfigurasi Model dari: {models_file.name}{RESET}")
    
    category_map = {
        "checkpoints": forge_path / "models" / "Stable-diffusion",
        "checkpoint": forge_path / "models" / "Stable-diffusion",
        "models": forge_path / "models" / "Stable-diffusion",
        "loras": forge_path / "models" / "Lora",
        "lora": forge_path / "models" / "Lora",
        "vaes": forge_path / "models" / "VAE",
        "vae": forge_path / "models" / "VAE",
        "controlnets": forge_path / "models" / "ControlNet",
        "controlnet": forge_path / "models" / "ControlNet",
        "upscalers": forge_path / "models" / "ESRGAN",
        "upscaler": forge_path / "models" / "ESRGAN",
        "embeddings": forge_path / "embeddings",
        "embedding": forge_path / "embeddings",
    }
    
    current_category = "checkpoints"
    total_processed = 0

    with open(models_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Deteksi section header [category]
            if line.startswith("[") and line.endswith("]"):
                current_category = line[1:-1].strip().lower()
                continue
            
            # Parsing URL & custom filename (URL -> custom_name.ext)
            if "->" in line:
                parts = line.split("->", 1)
                url = parts[0].strip()
                custom_filename = parts[1].strip()
            else:
                url = line
                custom_filename = None

            if not url.startswith("http://") and not url.startswith("https://"):
                continue

            target_folder = category_map.get(current_category, forge_path / "models" / "Stable-diffusion")

            if custom_filename:
                filename = custom_filename
            else:
                # Ambil nama file dari URL
                parsed = urlparse(url)
                path_name = os.path.basename(unquote(parsed.path))
                if path_name and ("." in path_name):
                    filename = path_name
                else:
                    filename = f"model_{int(time.time())}.safetensors"

            smart_download(url, target_folder / filename, desc=f"[{current_category.upper()}] {filename}")
            total_processed += 1

    if total_processed > 0:
        print(f"{GREEN}✓ Selesai memproses {total_processed} asset dari {models_file.name}.{RESET}")

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
    parser.add_argument("--models-file", default=None,
                        help="Path ke file models.txt (default: models.txt di direktori script)")
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

    # 1. Proses models.txt jika tersedia
    script_dir = Path(__file__).resolve().parent
    models_file = Path(args.models_file) if args.models_file else (script_dir / "models.txt")
    if models_file.exists():
        parse_models_file(models_file, forge_path)

    # 2. Proses --model-url jika diberikan via CLI
    models_dir = forge_path / "models" / "Stable-diffusion"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    if args.model_url:
        filename = args.model_url.split("/")[-1].split("?")[0] or "custom_model.safetensors"
        if not filename.endswith(".safetensors") and not filename.endswith(".ckpt"):
            filename += ".safetensors"
        smart_download(args.model_url, models_dir / filename, desc="[CHECKPOINT] Custom CLI")

    # 3. Fallback starter model jika folder checkpoint masih kosong
    existing_checkpoints = list(models_dir.glob("*.safetensors")) + list(models_dir.glob("*.ckpt"))
    if not existing_checkpoints and args.starter_model:
        starter_url = "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
        smart_download(starter_url, models_dir / "DreamShaper_8_pruned.safetensors", desc="[CHECKPOINT] Starter DreamShaper 8")
    elif existing_checkpoints:
        print(f"\n{GREEN}✓ Checkpoint model terdeteksi di Forge: {[f.name for f in existing_checkpoints]}{RESET}")

    launch_webui(forge_path, unknown)

if __name__ == "__main__":
    main()
