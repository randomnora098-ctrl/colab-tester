# Handout & Project Documentation: Colab Tester (Forge Neo Runner)

Dokumen ini berisi catatan lengkap arsitektur, progres yang telah dicapai, solusi teknis atas berbagai bug di Google Colab, serta panduan pemulihan (*recovery guide*) setelah instalasi ulang OS.

---

## 1. Gambaran Umum Proyek (Project Overview)
Proyek ini dirancang untuk mengotomatisasi instalasi, konfigurasi, pengunduhan model/ekstensi, dan eksekusi **Stable Diffusion WebUI Forge Neo** (`Haoming02/sd-webui-forge-classic`, branch `neo`) di **Google Colab (Free Tier - Tesla T4 16GB VRAM)**.

### Prinsip Alur Kerja (Zero-Edit Colab Workflow)
- Semua perubahan konfigurasi (kode, daftar model, daftar ekstensi, API key) dilakukan di repositori ini dan di-*push* ke GitHub (`main`).
- Pengguna **tidak perlu mengubah isi notebook Google Colab** setiap kali ingin mengganti model atau menambah ekstensi.
- Di Google Colab, cukup jalankan:
  ```bash
  # Setup awal (hanya sekali saat membuat sesi Colab baru)
  !git clone https://github.com/randomnora098-ctrl/colab-tester.git
  %cd colab-tester

  # Eksekusi atau update berikutnya
  !git pull && python forge_neo.py
  ```

---

## 2. Struktur File di Repository
| Nama File | Fungsi & Deskripsi |
| :--- | :--- |
| `forge_neo.py` | Script orkestrator utama untuk menjalankan Forge Neo di Google Colab. Menangani: pengecekan GPU/CPU, perbaikan *dependency conflict* Colab, instalasi `aria2c`, *smart download* model, instalasi ekstensi, injeksi Civitai API Key, dan peluncuran Gradio. |
| `models.txt` | Daftar URL model/asset yang akan diunduh otomatis menggunakan `aria2c` (16 *connections*) sebelum WebUI menyala. Mendukung kategori `[checkpoints]`, `[diffusion_models]`, `[loras]`, `[vaes]`, `[text_encoders]`, `[controlnets]`, `[upscalers]`, dan `[embeddings]`. |
| `extensions.txt` | Daftar URL Git ekstensi WebUI yang akan di-*clone* otomatis ke folder `extensions/`. |
| `GEMINI.md` | Konteks operasional dan instruksi standar untuk AI Agent (Antigravity / Gemini). |
| `test.py` | Script pengujian awal lingkungan GPU Google Colab. |
| `handout.md` | Dokumen catatan progres dan panduan pemulihan pasca instalasi ulang OS (file ini). |

---

## 3. Detail Progres & Fitur yang Telah Dibangun

### A. Smart Installer & Multi-Thread Downloader (`forge_neo.py`)
1. **Idempotent Execution (Aman Dijalankan Berulang Kali):**
   - Mengecek apakah `/content/forge-neo` sudah terinstal. Jika sudah ada, tidak akan mengkloning ulang dari awal.
   - Mengecek ukuran file model (>1 MB). Jika model sudah terunduh, proses unduh dilewati (*skip*).
   - Menginstal `aria2` secara otomatis untuk mengunduh file berukuran besar (GB) dengan kecepatan maksimal (`-x 16 -s 16`).
2. **Dukungan Multi-Kategori Model (`models.txt`):**
   - Mendukung penamaan file kustom dengan format: `<URL> -> <nama_file.safetensors>`.
   - Otomatis membuat *symlink* antara `models/text_encoder` dan `models/clip` agar model arsitektur baru (seperti Anima / Flux / Qwen) langsung terbaca oleh Forge Neo.

### B. Konfigurasi Model Saat Ini (`models.txt`)
Setelah menguji arsitektur **MOSS-Image** (yang menggunakan Qwen3.5 9B ~9.8 GB INT8 / ~19.3 GB BF16 dan terlalu berat untuk VRAM 16 GB milik Colab T4), konfigurasi dialihkan ke **Anima (2B DiT)** yang jauh lebih ringan namun memiliki kualitas setara:
- **Checkpoint Default:** DreamShaper 8 (`DreamShaper_8_pruned.safetensors`)
- **Anima VAE (`models/VAE/`):** `qwen_image_vae.safetensors` (~254 MB)
- **Anima Text Encoder (`models/text_encoder/`):** `qwen_3_06b_base.safetensors` (Qwen3 0.6B ~1.19 GB)
- **Auto-Cleanup MOSS:** `forge_neo.py` dilengkapi pembersih otomatis untuk menghapus sisa file MOSS-Image (`qwen3.5_9b_*.safetensors` dan `flux2-vae.safetensors`) jika masih ada di disk Colab.

### C. Ekstensi yang Terinstal (`extensions.txt`)
1. **CivBrowser** (`https://github.com/SignalFlagZ/sd-webui-civbrowser.git`) — Mencari dan mengunduh model Civitai langsung dari tab WebUI.
2. **SD-Hub** (`https://github.com/gutris1/sd-hub.git`) — *Batch downloader* cepat (Civitai/HuggingFace/GDrive), manajemen galeri, dan manajemen file.
3. **ADetailer** (`https://github.com/Bing-su/adetailer.git`) — Deteksi dan perbaikan otomatis wajah, mata, dan tangan berbasis YOLO.
4. **Tag Autocomplete** (`https://github.com/DominikDoom/a1111-sd-webui-tagcomplete.git`) — Auto-text / *autocomplete* tag Danbooru, e621, wildcards, dan LoRA saat mengetik prompt.

### D. Integrasi Otomatis Civitai API Key
- **API Key Aktif:** `916ff2c247a9be5f8f3b0d3974af7863`
- Diintegrasikan secara *native* ke dalam:
  1. `aria2c` downloader di `forge_neo.py` (otomatis menyisipkan `?token=...` saat mengunduh dari `civitai.com`).
  2. **CivBrowser:** Dipatch langsung ke `scripts/civsfz_settings.py`, `scripts/civsfz_ui.py`, dan `scripts/civsfz_api.py`.
  3. **SD-Hub:** Disimpan ke `/content/forge-neo/extensions/sd-hub/.sd-hub-config.json` dengan skema `{"Token": {"civitai-api-key": "..."}}` serta dipatch ke `sdhub/config.py` dan `sdhub/downloaderTab.py`.

---

## 4. Riwayat Masalah (Troubleshooting) & Solusi Teknis di `forge_neo.py`
Selama pengembangan di lingkungan Google Colab (Python 3.13), terdapat 5 masalah utama yang telah diselesaikan secara permanen di dalam `forge_neo.py`:

1. **Crash Gradio 6.x & `ModuleNotFoundError: No module named 'gradio_rangeslider'`**
   - *Penyebab:* Google Colab menginstal Gradio 6.31.0 secara bawaan, sedangkan Forge Neo membutuhkan Gradio 4.40.0 beserta komponen kustomnya.
   - *Solusi:* Fungsi `ensure_dependencies_compat()` otomatis mendeteksi versi Gradio dan menjalankan `pip install --force-reinstall "gradio==4.40.0" "gradio-rangeslider==0.0.8" "gradio-imageslider==0.0.20"`.

2. **Crash Protobuf & TensorFlow (`ImportError: cannot import name 'runtime_version' from 'google.protobuf'`)**
   - *Penyebab:* Library `transformers` mencoba mengimpor TensorFlow di Colab, namun versi `protobuf` tertimpa oleh paket lama (<5.26.1).
   - *Solusi:* Mengatur environment variable `TRANSFORMERS_NO_TF="1"` dan `USE_TF="0"`, serta memastikan `protobuf>=5.26.1` terinstal.

3. **Hang / Stuck pada Pesan `ALERT: You are updating from an old version... Press Enter to Continue...`**
   - *Penyebab:* Jika terdapat file `config.json` parsial sebelum Forge Neo pertama kali membuat skema konfigurasinya sendiri, Forge menganggap instalasi berasal dari versi lama dan meminta input `Enter` di terminal.
   - *Solusi:* Fungsi `clean_stale_configs()` menghapus `config.json` dan `ui-config.json` sebelum peluncuran, serta menyuntikkan設定 API langsung ke *source code* ekstensi alih-alih membuat `config.json` mentah.

4. **Error `launch.py: error: unrecognized arguments: --civsfz-api-key`**
   - *Penyebab:* Versi terbaru CivBrowser menghapus argumen CLI `--civsfz-api-key`, sehingga parser `launch.py` menolak argumen tersebut baik dari baris perintah maupun dari `COMMANDLINE_ARGS`.
   - *Solusi:* Menghapus argumen CLI tersebut dan menggantinya dengan *source patching* langsung pada modul Python CivBrowser.

5. **API Key Tidak Terbaca di SD-Hub**
   - *Penyebab:* SD-Hub tidak membaca `config.json` milik WebUI, melainkan membaca file khususnya sendiri di `.sd-hub-config.json`.
   - *Solusi:* Membuat file `/content/forge-neo/extensions/sd-hub/.sd-hub-config.json` dengan struktur JSON yang sesuai standar SD-Hub.

---

## 5. Panduan Setup Ulang Setelah Install Ulang OS (Post-Reinstall Recovery Guide)

Setelah Anda selesai menginstal ulang OS di komputer lokal Anda, ikuti langkah-langkah berikut untuk melanjutkan proyek ini:

### Langkah 1: Konfigurasi Git & SSH Key Baru
Karena kunci SSH lama (`id_ed25519`) tidak disimpan di GitHub demi keamanan (`.gitignore`), buat kunci SSH baru atau gunakan autentikasi GitHub di OS baru Anda:

```bash
# 1. Set identitas Git
git config --global user.name "randomnora098-ctrl"
git config --global user.email "randomnora098@gmail.com"

# 2. Buat SSH Key baru
ssh-keygen -t ed25519 -C "randomnora098@gmail.com" -f ~/.ssh/id_ed25519 -N ""

# 3. Tampilkan public key, lalu tambahkan ke GitHub -> Settings -> SSH and GPG keys
cat ~/.ssh/id_ed25519.pub
```

### Langkah 2: Clone Kembali Repository Ini
```bash
mkdir -p ~/.gemini/antigravity/scratch
cd ~/.gemini/antigravity/scratch
git clone git@github.com:randomnora098-ctrl/colab-tester.git
cd colab-tester
```
*(Catatan: Jika menggunakan Antigravity IDE di OS baru, Anda cukup meminta AI membaca file `handout.md` dan `GEMINI.md` di dalam folder ini agar AI langsung memahami seluruh riwayat proyek).*

### Langkah 3: Penggunaan di Google Colab
Di Google Colab, buat 1 cell kode dan jalankan:

```python
import os
if not os.path.exists("/content/colab-tester"):
    !git clone https://github.com/randomnora098-ctrl/colab-tester.git
%cd /content/colab-tester
!git pull && python forge_neo.py
```

---

## 6. Referensi Rekomendasi Model Ringan untuk Colab T4 (16GB VRAM)
1. **Anima (2B DiT)** — *Split model* (Checkpoint ~4-5GB + `qwen_3_06b_base.safetensors` 1.19GB + `qwen_image_vae.safetensors` 254MB). Sangat ringan untuk ukuran model DiT modern.
2. **Illustrious-XL (v1.0 / v1.1 / v2.0)** & finetune seperti **WAI-NSFW-illustrious-SDXL** / **Hassaku XL Illustrious** (~6.5 GB *All-in-One*). Sangat cepat di T4 dan pemahaman tag Danbooru terbaik.
3. **NoobAI-XL (Epsilon / V-Pred)** (~6.5 GB *All-in-One*). Sangat kuat di efek pencahayaan dan gaya artistik.
4. **CyberRealistic XL / Pony Realism** (~6.5 GB *All-in-One*). Pilihan terbaik untuk gaya semi-realistis / fotorealistis di T4.
