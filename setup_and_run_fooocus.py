import os
import re
import shutil
import subprocess
import torch

FOOOCUS_DIR = "."
REPO_URL = "https://github.com/lllyasviel/Fooocus"

# ---------- Funciones de utilidad ----------
def run(cmd, cwd=None):
    print(f"💻 Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)

def backup_file(path):
    if os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copy(path, backup_path)
        print(f"💾 Backup creado: {backup_path}")

def patch_file(path, patterns_replacements):
    if os.path.exists(path):
        backup_file(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for pattern, repl in patterns_replacements:
            content = re.sub(pattern, repl, content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ {path} parcheado")
    else:
        print(f"⚠️ Archivo no encontrado: {path}")

# ---------- 1️⃣ Clonar o actualizar repositorio ----------
if not os.path.exists(FOOOCUS_DIR):
    print("📦 Clonando Fooocus desde GitHub...")
    run(["git", "clone", REPO_URL, FOOOCUS_DIR])
else:
    print("🔄 Actualizando repositorio Fooocus...")
    run(["git", "pull"], cwd=FOOOCUS_DIR)

# ---------- 2️⃣ Actualizar dependencias críticas ----------
print("🔹 Instalando dependencias críticas...")
run(["pip", "install", "--upgrade", "gradio==4.44.1"])
run(["pip", "install", "einops==0.8.0"])

# ---------- 3️⃣ Instalar requirements.txt ----------
req_path = os.path.join(FOOOCUS_DIR, "requirements.txt")
if os.path.exists(req_path):
    print("🔹 Instalando requirements.txt de Fooocus...")
    run(["pip", "install", "-r", "requirements.txt"], cwd=FOOOCUS_DIR)
else:
    print("⚠️ No se encontró requirements.txt, saltando instalación de dependencias adicionales.")

# ---------- 4️⃣ Parchear webui.py ----------
webui_path = os.path.join(FOOOCUS_DIR, "webui.py")
patch_file(webui_path, [
    (r",\s*approved\s*=\s*[^,)]+", "")  # Elimina cualquier argumento approved=...
])

# ---------- 5️⃣ Parchear gradio_hijack.py ----------
grh_path = os.path.join(FOOOCUS_DIR, "modules/gradio_hijack.py")
patch_file(grh_path, [
    (r"\bIOComponent\b", "Component"),              # Reemplaza IOComponent por Component
    (r"from gradio\.deprecation import .*", ""),    # Elimina imports obsoletos
])

# ---------- 6️⃣ Detectar GPU y VRAM ----------
use_high_vram = False
disable_offload = True
device_str = "cpu"

if torch.cuda.is_available():
    total_vram = torch.cuda.get_device_properties(0).total_memory // (1024 ** 2)  # MB
    print(f"🔹 GPU detectada: {torch.cuda.get_device_name(0)} con {total_vram} MB VRAM")
    device_str = f"cuda:{torch.cuda.current_device()}"
    if total_vram >= 12000:  # 12 GB VRAM
        use_high_vram = True
        disable_offload = False
else:
    print("⚠️ No se detectó GPU. Se ejecutará en CPU.")

# ---------- 7️⃣ Construir comandos de ejecución ----------
cmd = ["python", "entry_with_update.py", "--share"]
if use_high_vram:
    cmd.append("--always-high-vram")
if disable_offload:
    cmd.append("--disable-offload")
cmd.append("--theme")
cmd.append("dark")

print("\n🎯 Ejecutando Fooocus con la configuración óptima para tu sistema...")
print(f"💻 Comando final: {' '.join(cmd)}")
run(cmd, cwd=FOOOCUS_DIR)
