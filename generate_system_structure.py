import os
from datetime import datetime

def analizar_sistema(ruta_inicio='.', archivo_salida='analisis_completo.txt'):
    # Use absolute path for output file to ensure we know where it is
    archivo_salida = os.path.abspath(archivo_salida)
    ruta_inicio = os.path.abspath(ruta_inicio)
    
    print(f"Iniciando análisis de: {ruta_inicio}")
    print(f"Guardando resultados en: {archivo_salida}")
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(f"ESTRUCTURA COMPLETA DEL SISTEMA - Generada el {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        
        for raiz, directorios, archivos in os.walk(ruta_inicio):
            # Calcular profundidad para la indentación
            try:
                # Handle potential path issues relative to start
                rel_path = os.path.relpath(raiz, ruta_inicio)
                if rel_path == '.':
                    nivel = 0
                else:
                    nivel = rel_path.count(os.sep) + 1
            except ValueError:
                nivel = 0
                
            indentado = ' ' * 4 * nivel
            f.write(f"{indentado}[DIR] {os.path.basename(raiz)}/\n")
            
            sub_indentado = ' ' * 4 * (nivel + 1)
            for nombre_archivo in archivos:
                ruta_completa = os.path.join(raiz, nombre_archivo)
                try:
                    # Obtenemos tamaño en KB para un análisis más pro
                    tamaño = os.path.getsize(ruta_completa) / 1024
                    f.write(f"{sub_indentado}{nombre_archivo} ({tamaño:.2f} KB)\n")
                except OSError:
                    f.write(f"{sub_indentado}{nombre_archivo} (Acceso denegado)\n")

    print(f"Análisis finalizado. Archivo guardado como: {archivo_salida}")

if __name__ == "__main__":
    # We analyze the current working directory which is the workspace root
    analizar_sistema('.')
