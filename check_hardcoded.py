#!/usr/bin/env python3
"""
Script para verificar que no quedan textos hardcodeados importantes
"""
import os
import re

def check_hardcoded_texts():
    """Verifica que no queden textos hardcodeados importantes"""

    # Textos que NO deberían estar hardcodeados (fuera de variables de entorno)
    hardcoded_patterns = [
        # Solo buscar en funciones, no en variables de configuración
        r'def.*:\s*.*""".*🤖.*"""',  # Funciones con docstrings largos
        r'def.*:\s*.*\'\'\'.*🎬.*\'\'\'',  # Funciones con docstrings largos
        r'await update\.message\.reply_text\(\s*"""',  # Mensajes hardcodeados en funciones
        r'await update\.message\.reply_text\(\s*\'\'\'',  # Mensajes hardcodeados en funciones
    ]

    files_to_check = ['bot.py', 'config.py']

    found_hardcoded = []

    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                for match in matches:
                    found_hardcoded.append({
                        'file': file_path,
                        'pattern': pattern,
                        'text': match[:100] + '...' if len(match) > 100 else match
                    })

    return found_hardcoded

def check_config_variables():
    """Verifica que todas las variables de configuración estén definidas"""

    required_vars = [
        'WELCOME_MESSAGE',
        'HELP_MESSAGE',
        'NO_CAPTION_MESSAGE',
        'PROCESSING_MESSAGE',
        'ACCESS_DENIED_MESSAGE'
    ]

    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()

    missing_vars = []
    for var in required_vars:
        if f'{var} = os.getenv(' not in content:
            missing_vars.append(var)

    return missing_vars

def main():
    print("🔍 VERIFICACIÓN: Código Hardcodeado Removido")
    print("=" * 60)

    # Verificar textos hardcodeados
    hardcoded = check_hardcoded_texts()
    if hardcoded:
        print("❌ TEXTOS HARDCODEADOS ENCONTRADOS:")
        for item in hardcoded:
            print(f"   📁 {item['file']}")
            print(f"   🔍 Patrón: {item['pattern']}")
            print(f"   📝 Texto: {item['text']}")
            print()
    else:
        print("✅ No se encontraron textos hardcodeados importantes")

    # Verificar variables de configuración
    print("\n📋 VERIFICACIÓN DE VARIABLES DE CONFIGURACIÓN:")
    missing = check_config_variables()
    if missing:
        print("❌ VARIABLES DE CONFIGURACIÓN FALTANTES:")
        for var in missing:
            print(f"   ❌ {var}")
    else:
        print("✅ Todas las variables de configuración están definidas")

    # Verificar que las variables se usen correctamente
    print("\n📋 VERIFICACIÓN DE USO DE VARIABLES:")
    with open('bot.py', 'r', encoding='utf-8') as f:
        bot_content = f.read()

    usage_checks = [
        ('Config.WELCOME_MESSAGE', 'Mensaje de bienvenida'),
        ('Config.HELP_MESSAGE', 'Mensaje de ayuda'),
        ('Config.NO_CAPTION_MESSAGE', 'Mensaje sin caption'),
        ('Config.PROCESSING_MESSAGE', 'Mensaje de procesamiento'),
        ('Config.ACCESS_DENIED_MESSAGE', 'Mensaje de acceso denegado')
    ]

    all_used = True
    for var, description in usage_checks:
        if var not in bot_content:
            print(f"   ❌ {description}: Variable no usada en bot.py")
            all_used = False
        else:
            print(f"   ✅ {description}: Variable correctamente usada")

    print("\n" + "=" * 60)
    if not hardcoded and not missing and all_used:
        print("🎉 ÉXITO TOTAL: Código completamente limpio")
        print("✅ Sin textos hardcodeados")
        print("✅ Todas las variables configuradas")
        print("✅ Todas las variables usadas correctamente")
        return True
    else:
        print("❌ PROBLEMAS ENCONTRADOS")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
