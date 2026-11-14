#!/usr/bin/env python3
"""
Forge Neo (sd-webui-forge-classic: neo branch) Launcher for Google Colab
Optimized for Tesla T4 GPU
Repo: https://github.com/Haoming02/sd-webui-forge-classic.git (branch: neo)
"""

import os
import sys

# Nonaktifkan TensorFlow pada HuggingFace Transformers untuk mencegah konflik Protobuf
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import subprocess
import shutil
import time
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

# Civitai API Key Default
DEFAULT_CIVITAI_KEY = "916ff2c247a9be5f8f3b0d3974af7863"

# Styling terminal
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
    has_gpu = False
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            print(f"{GREEN}✓ GPU Aktif: {device_name} ({vram_gb:.2f} GB VRAM){RESET}")
            if "T4" in device_name:
                print(f"{GREEN}✓ Optimalisasi Tesla T4 GPU diaktifkan.{RESET}")
            has_gpu = True
    except ImportError:
        pass

    if not has_gpu:
        print(f"\n{RED}{BOLD}" + "=" * 65)
        print("⚠️ PERINGATAN KRUSIAL: GPU TIDAK TERDETEKSI (RUNNING DI CPU)!")
        print("Forge Neo membutuhkan GPU T4 agar bisa berjalan cepat dan optimal.")
        print("Cara Mengaktifkan GPU di Google Colab:")
        print("  1. Buka menu atas: Runtime -> Change runtime type")
        print("  2. Pilih Hardware accelerator: T4 GPU")
        print("  3. Klik Save, lalu jalankan ulang sel notebook.")
        print("=" * 65 + f"{RESET}\n")
    return has_gpu

def is_forge_installed(forge_path):
    """Mengecek apakah Forge Neo dan dependensinya sudah terinstall."""
    marker = forge_path / ".installed_marker"
    launch_py = forge_path / "launch.py"
    return forge_path.exists() and launch_py.exists() and marker.exists()

def setup_directories(base_path):
    drive_mounted = os.path.exists("/content/drive/MyDrive")
    if drive_mounted:
        print(f"{GREEN}✓ Google Drive terdeteksi (/content/drive/MyDrive).{RESET}")
        drive_outputs = Path("/content/drive/MyDrive/Forge_Outputs")
        drive_outputs.mkdir(parents=True, exist_ok=True)
        
        # Symlink outputs ke Drive agar hasil gambar aman tersimpan
        local_outputs = base_path / "outputs"
        if not local_outputs.exists():
            local_outputs.symlink_to(drive_outputs)
            print(f"{GREEN}✓ Output ditautkan ke Google Drive: {drive_outputs}{RESET}")
    else:
        print(f"{YELLOW}ℹ Google Drive tidak dimount. Hasil render tersimpan di {base_path / 'outputs'}{RESET}")

def clone_forge_neo(target_dir):
    repo_url = "https://github.com/Haoming02/sd-webui-forge-classic.git"
    print(f"Mengkloning Forge Neo (branch: neo) ke {target_dir}...")
    cmd = ["git", "clone", "-b", "neo", "--depth", "1", repo_url, str(target_dir)]
    subprocess.run(cmd, check=True)
    print(f"{GREEN}✓ Selesai mengkloning Forge Neo.{RESET}")

def install_system_tools():
    """Install tool akselerasi (uv & aria2)."""
    # 1. Install uv
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)
        print(f"{GREEN}✓ `uv` siap digunakan.{RESET}")
    except Exception as e:
        print(f"{YELLOW}Gagal menginstall uv ({e}), menggunakan pip default.{RESET}")

    # 2. Install aria2 jika di Colab
    if shutil.which("aria2c") is None and os.path.exists("/usr/bin/apt-get"):
        print("Menginstall aria2 untuk multi-threaded download...")
        try:
            subprocess.run(["apt-get", "update", "-qq"], check=False)
            subprocess.run(["apt-get", "install", "-y", "-qq", "aria2"], check=False)
            if shutil.which("aria2c"):
                print(f"{GREEN}✓ aria2c siap digunakan.{RESET}")
        except Exception:
            pass

def install_forge_requirements(forge_path):
    """Instalasi dependensi python Forge Neo."""
    print("Memasang dependensi requirements Forge Neo...")
    req_file = forge_path / "requirements_versions.txt"
    if not req_file.exists():
        req_file = forge_path / "requirements.txt"
        
    if req_file.exists():
        if shutil.which("uv"):
            cmd = ["uv", "pip", "install", "--system", "-r", str(req_file)]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)]
        try:
            subprocess.run(cmd, check=False)
            print(f"{GREEN}✓ Requirements berhasil dipasang.{RESET}")
        except Exception as e:
            print(f"{YELLOW}Warning saat install requirements: {e}{RESET}")

def ensure_dependencies_compat():
    """
    Memastikan Gradio 4.40.0 dan Protobuf modern (>=5.26.1) terpasang.
    Mencegah crash 'cannot import name runtime_version from google.protobuf'.
    """
    need_fix = False
    try:
        import gradio
        if getattr(gradio, "__version__", "") != "4.40.0":
            need_fix = True
        import gradio_rangeslider
        import gradio_imageslider
        import google.protobuf
        from google.protobuf import runtime_version
    except (ImportError, Exception):
        need_fix = True

    if need_fix:
        print(f"\n{YELLOW}🔧 Menyelaraskan dependensi Colab (Gradio 4.40.0, Protobuf >= 5.26.1)...{RESET}")
        pkgs = [
            "gradio==4.40.0",
            "gradio-rangeslider==0.0.8",
            "gradio-imageslider==0.0.20",
            "protobuf>=5.26.1"
        ]
        cmd = [sys.executable, "-m", "pip", "install", "-q", "--force-reinstall"] + pkgs
        try:
            subprocess.run(cmd, check=True)
            print(f"{GREEN}✓ Gradio 4.40.0 & Protobuf (modern) berhasil diselaraskan!{RESET}")
        except Exception as e:
            print(f"{YELLOW}Warning saat menyelaraskan dependensi: {e}{RESET}")

def mark_installed(forge_path):
    marker = forge_path / ".installed_marker"
    with open(marker, "w", encoding="utf-8") as f:
        f.write(f"Installed on: {time.ctime()}\nVersion: neo\n")
    print(f"{GREEN}✓ Status instalasi disimpan ke {marker.name}.{RESET}")

def perform_full_installation(forge_path, force=False):
    """Melakukan alur instalasi lengkap."""
    if force and forge_path.exists():
        print(f"{YELLOW}Menghapus instalasi lama untuk instalasi ulang bersih...{RESET}")
        shutil.rmtree(forge_path, ignore_errors=True)

    print(f"\n{BOLD}[2/5] Melakukan Instalasi Forge Neo & Dependensi...{RESET}")
    clone_forge_neo(forge_path)
    setup_directories(forge_path)
    install_system_tools()
    install_forge_requirements(forge_path)
    ensure_dependencies_compat()
    mark_installed(forge_path)
    print(f"\n{GREEN}{BOLD}🎉 Instalasi Forge Neo Selesai 100%!{RESET}\n")

def configure_civitai_api(forge_path, api_key):
    """Mengintegrasikan Civitai API Key ke CivBrowser, SD-Hub, dan WebUI settings."""
    if not api_key:
        return

    print(f"\n{BOLD}🔑 Mengonfigurasi Civitai API Key ke CivBrowser & SD-Hub...{RESET}")
    
    # 1. Update config.json di root WebUI Forge (untuk CivBrowser & UI)
    config_file = forge_path / "config.json"
    config_data = {}
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {}

    config_data["civsfz_api_key"] = api_key
    config_data["civitai_api_key"] = api_key
    config_data["sd_hub_civitai_api_key"] = api_key
    config_data["sdhub_civitai_api_key"] = api_key

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        print(f"{GREEN}✓ API Key disematkan ke config.json (CivBrowser & WebUI).{RESET}")
    except Exception as e:
        print(f"{YELLOW}Warning saat menulis config.json: {e}{RESET}")

    # 2. Update konfigurasi token SD-Hub
    sd_hub_dirs = [
        forge_path,
        forge_path / "extensions" / "sd-hub",
        forge_path / "extensions" / "sdhub"
    ]
    token_filenames = [
        ".sd-hub-token.json",
        "sd-hub-token.json",
        ".sd-hub-config.json",
        "sd-hub-config.json"
    ]
    token_payload = {
        "civitai": api_key,
        "civitai_api_key": api_key,
        "civitai_token": api_key,
        "token": api_key
    }

    for d in sd_hub_dirs:
        if d.exists():
            for fname in token_filenames:
                t_path = d / fname
                try:
                    existing = {}
                    if t_path.exists():
                        try:
                            with open(t_path, "r", encoding="utf-8") as f:
                                existing = json.load(f)
                        except Exception:
                            existing = {}
                    existing.update(token_payload)
                    with open(t_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)
                except Exception:
                    pass
    print(f"{GREEN}✓ API Key berhasil dikonfigurasi untuk SD-Hub.{RESET}")

def smart_download(url, dest_file, desc="Asset", civitai_key=None):
    """Download menggunakan aria2c (jika ada) atau curl dengan resume support dan Civitai token auth."""
    dest_file = Path(dest_file)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Cek apakah file sudah ada dan ukurannya > 1MB
    if dest_file.exists() and dest_file.stat().st_size > 1024 * 1024:
        size_mb = dest_file.stat().st_size / (1024 * 1024)
        print(f"{GREEN}✓ {desc} sudah ada: {dest_file.name} ({size_mb:.1f} MB) -> Dilewati.{RESET}")
        return

    # Sertakan Civitai token jika URL dari civitai.com
    headers = []
    if civitai_key and "civitai.com" in url:
        if "token=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={civitai_key}"
        headers.append(f"Authorization: Bearer {civitai_key}")

    print(f"Mengunduh {desc}: {dest_file.name}...")
    
    if shutil.which("aria2c"):
        cmd = [
            "aria2c",
            "--console-log-level=error",
            "-c", "-x", "16", "-s", "16", "-k", "1M",
            "-d", str(dest_file.parent),
            "-o", dest_file.name,
        ]
        for h in headers:
            cmd.extend(["--header", h])
        cmd.append(url)
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print(f"{GREEN}✓ Selesai mengunduh {desc}: {dest_file.name}{RESET}")
            return
        else:
            print(f"{YELLOW}aria2c gagal, mencoba fallback ke curl...{RESET}")

    # Fallback curl
    cmd = ["curl", "-L", "-C", "-"]
    for h in headers:
        cmd.extend(["-H", h])
    cmd.extend(["-o", str(dest_file), url])
    subprocess.run(cmd, check=True)
    print(f"{GREEN}✓ Selesai mengunduh {desc}: {dest_file.name}{RESET}")

def parse_models_file(models_file_path, forge_path, civitai_key=None):
    """Membaca models.txt dan mendownload asset baru."""
    models_file = Path(models_file_path)
    if not models_file.exists():
        return

    print(f"\n{BOLD}[3/5] Memeriksa Model & Asset dari {models_file.name}...{RESET}")
    
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
                parsed = urlparse(url)
                path_name = os.path.basename(unquote(parsed.path))
                if path_name and ("." in path_name):
                    filename = path_name
                else:
                    filename = f"model_{int(time.time())}.safetensors"

            smart_download(url, target_folder / filename, desc=f"[{current_category.upper()}] {filename}", civitai_key=civitai_key)
            total_processed += 1

def setup_extensions(forge_path, extensions_file_path, update=False):
    """Membaca extensions.txt dan mengkloning atau memperbarui ekstensi."""
    ext_file = Path(extensions_file_path)
    if not ext_file.exists():
        return

    ext_dir = forge_path / "extensions"
    ext_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{BOLD}[4/5] Memeriksa & Memasang Ekstensi dari {ext_file.name}...{RESET}")
    total_ext = 0

    with open(ext_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "->" in line:
                parts = line.split("->", 1)
                url = parts[0].strip()
                folder_name = parts[1].strip()
            else:
                url = line
                folder_name = url.rstrip("/").split("/")[-1].replace(".git", "")

            if not url.startswith("http://") and not url.startswith("https://"):
                continue

            target_ext_path = ext_dir / folder_name

            if not target_ext_path.exists():
                print(f"Mengkloning ekstensi: {folder_name}...")
                cmd = ["git", "clone", "--depth", "1", url, str(target_ext_path)]
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    print(f"{GREEN}✓ Ekstensi {folder_name} berhasil dipasang.{RESET}")
                    # Cek requirements.txt spesifik milik ekstensi
                    req_path = target_ext_path / "requirements.txt"
                    if req_path.exists():
                        print(f"  Memasang requirement untuk {folder_name}...")
                        cmd_req = ["uv", "pip", "install", "--system", "-r", str(req_path)] if shutil.which("uv") else [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_path)]
                        subprocess.run(cmd_req, check=False)
                else:
                    print(f"{RED}Gagal mengkloning ekstensi {folder_name}{RESET}")
            else:
                print(f"{GREEN}✓ Ekstensi {folder_name} sudah terpasang.{RESET}")
                if update:
                    print(f"  Memperbarui {folder_name} (git pull)...")
                    subprocess.run(["git", "-C", str(target_ext_path), "pull"], check=False)

            total_ext += 1

    # Khusus ADetailer: Pastikan ultralytics terpasang
    if (ext_dir / "adetailer").exists():
        try:
            import ultralytics
        except ImportError:
            print("Memasang dependensi `ultralytics` untuk ADetailer (YOLO)...")
            cmd_yolo = ["uv", "pip", "install", "--system", "ultralytics"] if shutil.which("uv") else [sys.executable, "-m", "pip", "install", "-q", "ultralytics"]
            subprocess.run(cmd_yolo, check=False)

    if total_ext > 0:
        print(f"{GREEN}✓ Seluruh ekstensi ({total_ext}) siap digunakan!{RESET}")

def launch_webui(forge_dir, extra_args, has_gpu=True, civitai_key=None):
    print(f"\n{BOLD}[5/5] Menjalankan Forge Neo WebUI...{RESET}")
    
    # Argumen optimasi Google Colab
    launch_args = [
        sys.executable,
        "launch.py",
        "--share",                           # Wajib untuk link gradio.live di Colab
        "--enable-insecure-extension-access", # Mengizinkan install extensions via UI
        "--theme", "dark",                   # Tema gelap
        "--skip-version-check",              # Nonaktifkan version check warning
    ]
    
    # Sertakan Civitai API key untuk CivBrowser
    if civitai_key:
        launch_args.extend(["--civsfz-api-key", civitai_key])

    if has_gpu:
        launch_args.extend([
            "--cuda-stream",                 # Optimasi stream CUDA
            "--pin-shared-memory"            # Kecepatan swap memori
        ])
    else:
        launch_args.extend([
            "--use-cpu", "all",
            "--no-half",
            "--skip-torch-cuda-test"
        ])

    if extra_args:
        launch_args.extend(extra_args)
        
    # Pastikan env var nonaktifkan TF & Civitai API diteruskan ke child process
    env = os.environ.copy()
    env["TRANSFORMERS_NO_TF"] = "1"
    env["USE_TF"] = "0"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"
    if civitai_key:
        env["CIVITAI_API_KEY"] = civitai_key
        env["CIVITAI_TOKEN"] = civitai_key

    print(f"Perintah eksekusi:")
    print(f"{CYAN}{' '.join(launch_args)}{RESET}\n")
    print(f"{YELLOW}👉 Perhatikan output di bawah hingga link `https://xxxxxxxx.gradio.live` muncul.{RESET}")
    print(f"{YELLOW}👉 Buka link publik tersebut untuk menggunakan WebUI Forge Neo.{RESET}\n")
    
    os.chdir(forge_dir)
    subprocess.run(launch_args, env=env)

def main():
    parser = argparse.ArgumentParser(description="Forge Neo Launcher untuk Colab T4 GPU")
    parser.add_argument("--dir", default="/content/forge-neo" if os.path.exists("/content") else "./forge-neo", 
                        help="Lokasi instalasi Forge Neo")
    parser.add_argument("--models-file", default=None,
                        help="Path ke file models.txt")
    parser.add_argument("--extensions-file", default=None,
                        help="Path ke file extensions.txt")
    parser.add_argument("--civitai-api-key", default=DEFAULT_CIVITAI_KEY,
                        help="Civitai API Key untuk CivBrowser, SD-Hub, dan download model")
    parser.add_argument("--model-url", default=None, 
                        help="URL file model (.safetensors) langsung")
    parser.add_argument("--starter-model", action="store_true",
                        help="Unduh model starter (DreamShaper 8 SD1.5) jika belum ada model")
    parser.add_argument("--force-reinstall", action="store_true",
                        help="Paksa instal ulang bersih Forge Neo & dependensi")
    parser.add_argument("--update", action="store_true",
                        help="Perbarui repo Forge Neo & seluruh ekstensi ke commit terbaru")
    args, unknown = parser.parse_known_args()

    banner()
    has_gpu = check_environment()
    
    forge_path = Path(args.dir).resolve()

    # Logika Cek Status Instalasi
    if not is_forge_installed(forge_path) or args.force_reinstall:
        print(f"\n{YELLOW}⚡ Status: Forge Neo belum terinstall.{RESET}")
        print(f"Memulai proses instalasi lengkap beserta requirements...")
        perform_full_installation(forge_path, force=args.force_reinstall)
    else:
        print(f"\n{GREEN}{BOLD}⚡ Status: Forge Neo & seluruh requirement SUDAH TERINSTALL!{RESET}")
        print(f"{CYAN}⏩ Melewati proses instalasi. Langsung menuju persiapan running...{RESET}")
        setup_directories(forge_path)
        ensure_dependencies_compat()
        if args.update:
            print("Memperbarui kode Forge Neo...")
            subprocess.run(["git", "-C", str(forge_path), "pull"], check=False)

    script_dir = Path(__file__).resolve().parent

    # 1. Konfigurasi Civitai API Key ke CivBrowser & SD-Hub
    configure_civitai_api(forge_path, args.civitai_api_key)

    # 2. Cek & Unduh model dari models.txt
    models_file = Path(args.models_file) if args.models_file else (script_dir / "models.txt")
    if models_file.exists():
        parse_models_file(models_file, forge_path, civitai_key=args.civitai_api_key)

    # 3. Cek --model-url CLI
    models_dir = forge_path / "models" / "Stable-diffusion"
    models_dir.mkdir(parents=True, exist_ok=True)
    if args.model_url:
        filename = args.model_url.split("/")[-1].split("?")[0] or "custom_model.safetensors"
        if not filename.endswith(".safetensors") and not filename.endswith(".ckpt"):
            filename += ".safetensors"
        smart_download(args.model_url, models_dir / filename, desc="[CHECKPOINT] Custom CLI", civitai_key=args.civitai_api_key)

    # 4. Fallback starter model jika folder checkpoint kosong
    existing_checkpoints = list(models_dir.glob("*.safetensors")) + list(models_dir.glob("*.ckpt"))
    if not existing_checkpoints and args.starter_model:
        starter_url = "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
        smart_download(starter_url, models_dir / "DreamShaper_8_pruned.safetensors", desc="[CHECKPOINT] Starter DreamShaper 8")
    elif existing_checkpoints:
        print(f"{GREEN}✓ Checkpoint model terdeteksi di Forge: {[f.name for f in existing_checkpoints]}{RESET}")

    # 5. Cek & Pasang ekstensi dari extensions.txt
    extensions_file = Path(args.extensions_file) if args.extensions_file else (script_dir / "extensions.txt")
    if extensions_file.exists():
        setup_extensions(forge_path, extensions_file, update=args.update)

    # Pastikan konfigurasi token SD-Hub diperbarui kembali setelah ekstensi terkloning
    configure_civitai_api(forge_path, args.civitai_api_key)

    # 6. Langsung jalankan WebUI!
    launch_webui(forge_path, unknown, has_gpu=has_gpu, civitai_key=args.civitai_api_key)

if __name__ == "__main__":
    main()
