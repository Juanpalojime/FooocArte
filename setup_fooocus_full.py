import os
import re
import shutil
import subprocess

FOOOCUS_DIR = "./FooocArte"  # Cambia si tu carpeta principal es diferente
REPO_URL = "https://github.com/lllyasviel/Fooocus"  # URL del repositorio oficial

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

# ---------- 6️⃣ Mensaje final ----------
print("\n🎯 Configuración completa. Ahora puedes ejecutar Fooocus así:")
print(f"cd {FOOOCUS_DIR}")
print("python entry_with_update.py --share --always-high-vram --disable-offload --theme dark")
