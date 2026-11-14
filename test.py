import sys
import platform
import time

print("=" * 50)
print("🚀 SCRIPT BERHASIL DIJALANKAN DI GOOGLE COLAB!")
print("=" * 50)

print(f"Python Version : {sys.version.split()[0]}")
print(f"OS Platform    : {platform.system()} {platform.release()}")

try:
    import torch
    print(f"PyTorch Version: {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available : {cuda_available}")
    
    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        print(f"GPU Device     : {device_name} (Total: {device_count})")
        print("\n⚡ Melakukan uji coba komputasi tensor di GPU...")
        
        # Test tensor operation on GPU
        x = torch.randn(5000, 5000, device="cuda")
        start = time.time()
        y = torch.matmul(x, x)
        torch.cuda.synchronize()
        duration = time.time() - start
        
        print(f"✅ Uji coba perkalian matriks 5000x5000 selesai dalam {duration:.4f} detik!")
    else:
        print("⚠️ GPU tidak terdeteksi. Pastikan Anda memilih Runtime -> Change runtime type -> T4 GPU di Colab.")

except ImportError:
    print("PyTorch belum terinstall di environment ini.")

print("=" * 50)
print("🎉 Loop alur kerja GitHub -> Colab berfungsi normal!")
print("=" * 50)
