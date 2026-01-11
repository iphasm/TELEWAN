#!/usr/bin/env python3
"""
Script de prueba específico para TikTok
"""
import subprocess
import os
import uuid

def test_tiktok_download():
    """Prueba la descarga de un video de TikTok con la configuración actualizada"""

    # Crear directorio temporal si no existe
    temp_dir = './temp_test'
    os.makedirs(temp_dir, exist_ok=True)

    # Video de prueba de TikTok (uno público y conocido)
    test_url = "https://www.tiktok.com/@tiktok/video/7106594312295894278"  # Video oficial de TikTok

    # Generar nombre único para el archivo
    video_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(temp_dir, f'test_tiktok_{video_id}.%(ext)s')

    # Comando yt-dlp optimizado para TikTok
    cmd = [
        'yt-dlp',
        '--no-check-certificates',
        '--no-playlist',
        '--max-filesize', '50M',  # Límite más pequeño para prueba
        '--format', 'best[height<=720]',
        '--output', output_template,
        '--print', '%(title)s',
        '--print', '%(duration)s',
        '--print', '%(ext)s',
        # Configuración específica para TikTok
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--add-header', 'Referer: https://www.tiktok.com/',
        '--extractor-args', 'tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com;app_info=7355728852457084934',
        test_url
    ]

    print("🧪 Probando descarga de TikTok...")
    print(f"📥 URL: {test_url}")
    print(f"📁 Output: {output_template}")
    print(f"⚙️ Comando: {' '.join(cmd[:5])} ... {cmd[-1]}")
    print()

    try:
        # Ejecutar comando
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minuto para prueba
        )

        print(f"📊 Código de salida: {result.returncode}")
        print(f"📝 Salida estándar:")
        print(result.stdout)
        print()

        if result.stderr:
            print(f"⚠️ Errores:")
            print(result.stderr)
            print()

        # Verificar si se creó el archivo
        if result.returncode == 0:
            # Buscar archivo creado
            for file in os.listdir(temp_dir):
                if file.startswith(f'test_tiktok_{video_id}'):
                    filepath = os.path.join(temp_dir, file)
                    size = os.path.getsize(filepath)
                    print(f"✅ Archivo creado: {filepath} ({size:,} bytes)")

                    # Limpiar archivo de prueba
                    os.remove(filepath)
                    break
            else:
                print("❌ No se encontró archivo de salida")
        else:
            print("❌ Comando falló")

    except subprocess.TimeoutExpired:
        print("⏰ Timeout: La descarga tomó demasiado tiempo")
    except Exception as e:
        print(f"💥 Error: {e}")

    # Limpiar directorio temporal
    try:
        os.rmdir(temp_dir)
        print("🧹 Directorio temporal limpiado")
    except:
        pass

if __name__ == "__main__":
    test_tiktok_download()
