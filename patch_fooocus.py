import os
import re
import shutil
import subprocess

# ---------- 1️⃣ Actualizar dependencias ----------
print("🔹 Actualizando Gradio y einops...")
subprocess.run(["pip", "install", "--upgrade", "gradio==4.44.1"], check=True)
subprocess.run(["pip", "install", "einops==0.8.0"], check=True)

# Función para hacer backup antes de modificar
def backup_file(path):
    if os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copy(path, backup_path)
        print(f"💾 Backup creado: {backup_path}")

# ---------- 2️⃣ Arreglar webui.py ----------
webui_path = "./webui.py"
if os.path.exists(webui_path):
    backup_file(webui_path)
    with open(webui_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Elimina cualquier argumento 'approved=...'
    fixed_content = re.sub(r",\s*approved\s*=\s*[^,)]+", "", content)
    
    with open(webui_path, "w", encoding="utf-8") as f:
        f.write(fixed_content)
    print(f"✅ webui.py corregido (removed 'approved')")

# ---------- 3️⃣ Arreglar gradio_hijack.py ----------
grh_path = "./modules/gradio_hijack.py"
if os.path.exists(grh_path):
    backup_file(grh_path)
    with open(grh_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1️⃣ Reemplaza IOComponent por Component
    content = re.sub(r"\bIOComponent\b", "Component", content)
    
    # 2️⃣ Elimina imports de gradio.deprecation que ya no existen
    content = re.sub(r"from gradio\.deprecation import .*", "", content)
    
    with open(grh_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ gradio_hijack.py corregido (IOComponent y deprecated imports)")

print("🎯 Reparaciones completadas. Ahora ejecuta:")
print("python entry_with_update.py --share --always-high-vram --disable-offload --theme dark")
