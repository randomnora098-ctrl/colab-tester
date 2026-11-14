# Project: Colab Tester & GPU Runner

## Context & Workflow
- **Path Lokal:** `/home/ryan/.gemini/antigravity/scratch/colab-tester`
- **GitHub Remote:** `git@github.com:randomnora098-ctrl/colab-tester.git`
- **User GitHub:** `randomnora098-ctrl` (`randomnora098@gmail.com`)
- **Kunci SSH:** `/home/ryan/.gemini/antigravity/scratch/colab-tester/id_ed25519`
- **SSH Command:** `ssh -F /dev/null -i /home/ryan/.gemini/antigravity/scratch/colab-tester/id_ed25519 -o StrictHostKeyChecking=accept-new`

## Standar Operasi
1. Semua logika kode ditulis di file `.py` di dalam folder ini.
2. Konfigurasi model/LoRA/VAE ditulis di `models.txt`.
3. Konfigurasi ekstensi WebUI ditulis di `extensions.txt`.
4. Saat ada pembaruan kode, model, atau ekstensi, langsung lakukan commit dan push ke `main`.
5. Di Google Colab, user cukup menjalankan:
   ```bash
   !git pull && python <nama_script>.py
   ```
   Contoh Forge Neo:
   ```bash
   !git pull && python forge_neo.py
   ```
