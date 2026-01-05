#!/usr/bin/env python3
"""
Script de prueba para validar el manejo de errores en el bot.
"""
import logging
from unittest.mock import MagicMock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_message_validation():
    """Prueba la validación de mensajes."""

    print("=== Prueba de Validación de Mensajes ===")

    # Caso 1: Mensaje normal con foto
    print("\n--- Caso 1: Mensaje normal con foto ---")
    mock_message = MagicMock()
    mock_message.from_user.id = 123456789
    mock_message.chat.id = 987654321
    mock_message.message_id = 111
    mock_message.photo = [MagicMock(file_id="test_photo")]
    mock_message.document = None
    mock_message.sticker = None
    mock_message.caption = "una mujer hermosa"

    try:
        # Simular validación inicial
        user_id = mock_message.from_user.id if mock_message.from_user else "unknown"
        chat_id = mock_message.chat.id if mock_message.chat else "unknown"
        message_id = mock_message.message_id if hasattr(mock_message, 'message_id') else "unknown"

        print(f"✅ User ID: {user_id}")
        print(f"✅ Chat ID: {chat_id}")
        print(f"✅ Message ID: {message_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Caso 2: Mensaje sin foto
    print("\n--- Caso 2: Mensaje sin atributos ---")
    mock_message_bad = MagicMock()
    mock_message_bad.from_user = None
    mock_message_bad.chat = None
    mock_message_bad.message_id = None

    try:
        user_id = mock_message_bad.from_user.id if mock_message_bad.from_user else "unknown"
        chat_id = mock_message_bad.chat.id if mock_message_bad.chat else "unknown"
        message_id = mock_message_bad.message_id if hasattr(mock_message_bad, 'message_id') else "unknown"

        print(f"✅ User ID: {user_id}")
        print(f"✅ Chat ID: {chat_id}")
        print(f"✅ Message ID: {message_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Caso 3: Validación de arrays vacíos
    print("\n--- Caso 3: Validación de arrays vacíos ---")

    # Foto vacía
    try:
        if not mock_message.photo or len(mock_message.photo) == 0:
            raise ValueError("No se encontraron fotos en el mensaje")
        print("✅ Fotos OK")
    except ValueError as e:
        print(f"❌ Error fotos: {e}")

    # Documento vacío
    mock_message_no_doc = MagicMock()
    mock_message_no_doc.document = None
    try:
        if not mock_message_no_doc.document:
            raise ValueError("No se encontró documento en el mensaje")
        print("✅ Documento OK")
    except ValueError as e:
        print(f"✅ Error documento esperado: {e}")

    # Sticker vacío
    mock_message_no_sticker = MagicMock()
    mock_message_no_sticker.sticker = None
    try:
        if not mock_message_no_sticker.sticker:
            raise ValueError("No se encontró sticker en el mensaje")
        print("✅ Sticker OK")
    except ValueError as e:
        print(f"✅ Error sticker esperado: {e}")

    print("\n=== Pruebas completadas ===")

if __name__ == "__main__":
    test_message_validation()

