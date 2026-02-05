import os
import re
import subprocess

# ---------- 1️⃣ Actualizar dependencias ----------
print("🔹 Actualizando Gradio y einops...")
subprocess.run(["pip", "install", "--upgrade", "gradio==4.44.1"], check=True)
subprocess.run(["pip", "install", "einops==0.8.0"], check=True)

# ---------- 2️⃣ Arreglar webui.py ----------
webui_path = "./webui.py"
if os.path.exists(webui_path):
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
    with open(grh_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Reemplaza IOComponent por Component
    fixed_content = re.sub(r"\bIOComponent\b", "Component", content)
    
    with open(grh_path, "w", encoding="utf-8") as f:
        f.write(fixed_content)
    print(f"✅ gradio_hijack.py corregido (IOComponent -> Component)")

print("🎯 Reparaciones completadas. Ahora ejecuta:")
print("python entry_with_update.py --share --always-high-vram --disable-offload --theme dark")
