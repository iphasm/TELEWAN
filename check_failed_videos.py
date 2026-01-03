#!/usr/bin/env python3
"""
Script para verificar y recuperar videos que se generaron pero no se enviaron
Ejecutar manualmente cuando se detecten videos faltantes
"""

import os
import requests
from datetime import datetime, timedelta
import json

# Configuración
WAVESPEED_API_KEY = os.getenv("WAVESPEED_API_KEY")
WAVESPEED_BASE_URL = os.getenv("WAVESPEED_BASE_URL", "https://api.wavespeed.ai")

def check_recent_requests():
    """
    Función hipotética para verificar solicitudes recientes
    En una implementación real, necesitarías acceso a logs o base de datos
    """
    print("🔍 Verificando videos pendientes de envío...")
    print("Esta función requiere implementación específica según tu setup de logging")
    print("Posibles lugares para verificar:")
    print("- Logs de Railway")
    print("- Archivos en /app/storage/")
    print("- Base de datos si tienes una")

def recover_video_by_id(request_id: str):
    """
    Intentar recuperar un video específico por su request_id
    """
    if not WAVESPEED_API_KEY:
        print("❌ WAVESPEED_API_KEY no configurada")
        return

    url = f"{WAVESPEED_BASE_URL}/api/v3/predictions/{request_id}/result"
    headers = {"Authorization": f"Bearer {WAVESPEED_API_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('data'):
                task_data = result['data']
                status = task_data.get('status')

                if status == 'completed' and task_data.get('outputs'):
                    video_url = task_data['outputs'][0]
                    print(f"✅ Video encontrado: {video_url}")

                    # Descargar el video
                    video_response = requests.get(video_url)
                    if video_response.status_code == 200:
                        # Guardar el video
                        filename = f"recovered_{request_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        with open(filename, 'wb') as f:
                            f.write(video_response.content)
                        print(f"💾 Video guardado como: {filename}")
                        return filename
                    else:
                        print(f"❌ Error descargando video: {video_response.status_code}")
                else:
                    print(f"❌ Video no completado. Status: {status}")
            else:
                print("❌ No se encontraron datos para este request_id")
        else:
            print(f"❌ Error en la API: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🎬 Herramienta de Recuperación de Videos TELEWAN")
    print("=" * 50)

    if len(os.sys.argv) > 1:
        request_id = os.sys.argv[1]
        print(f"🔍 Buscando video con request_id: {request_id}")
        recover_video_by_id(request_id)
    else:
        check_recent_requests()
        print("\n💡 Uso: python check_failed_videos.py <request_id>")
        print("   Ejemplo: python check_failed_videos.py abc123def456")

if __name__ == "__main__":
    main()
