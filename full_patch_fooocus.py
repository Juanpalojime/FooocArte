import os
import re
import shutil
import subprocess

# ---------- Funciones de utilidad ----------
def run(cmd):
    print(f"💻 Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

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

# ---------- 1️⃣ Actualizar dependencias críticas ----------
print("🔹 Actualizando dependencias críticas...")
run(["pip", "install", "--upgrade", "gradio==4.44.1"])
run(["pip", "install", "einops==0.8.0"])

# ---------- 2️⃣ Instalar requirements de Fooocus ----------
if os.path.exists("requirements.txt"):
    print("🔹 Instalando requirements.txt de Fooocus...")
    run(["pip", "install", "-r", "requirements.txt"])
else:
    print("⚠️ No se encontró requirements.txt. Saltando esta parte.")

# ---------- 3️⃣ Parchear webui.py ----------
webui_path = "./webui.py"
patch_file(webui_path, [
    (r",\s*approved\s*=\s*[^,)]+", "")  # Elimina cualquier argumento approved=...
])

# ---------- 4️⃣ Parchear gradio_hijack.py ----------
grh_path = "./modules/gradio_hijack.py"
patch_file(grh_path, [
    (r"\bIOComponent\b", "Component"),              # Reemplaza IOComponent por Component
    (r"from gradio\.deprecation import .*", ""),    # Elimina imports obsoletos
])

# ---------- 5️⃣ Mensaje final ----------
print("\n🎯 Reparaciones completas. Ahora ejecuta Fooocus así:")
print("python entry_with_update.py --share --always-high-vram --disable-offload --theme dark")
