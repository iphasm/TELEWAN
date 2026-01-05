#!/usr/bin/env python3
"""
Script de prueba para verificar el comportamiento de procesamiento duplicado.
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simular las importaciones necesarias
class MockUpdate:
    def __init__(self, message_text="", has_photo=False, has_caption=False):
        self.effective_chat = MagicMock()
        self.effective_chat.id = 123456789
        self.effective_user = MagicMock()
        self.effective_user.id = 987654321

        self.message = MagicMock()
        self.message.from_user.id = 987654321
        self.message.chat.id = 123456789
        self.message.message_id = 1
        self.message.caption = message_text if has_caption else None

        if has_photo:
            self.message.photo = [MagicMock(file_id="test_photo")]
        else:
            self.message.photo = None
        self.message.document = None
        self.message.sticker = None

class MockContext:
    def __init__(self):
        self.user_data = {}
        self.bot = AsyncMock()

def test_duplicate_prevention():
    """Prueba la lógica de prevención de duplicados."""

    print("=== Prueba de Prevención de Procesamiento Duplicado ===")

    # Simular dos mensajes idénticos
    update1 = MockUpdate(has_photo=True, has_caption=False)
    update2 = MockUpdate(has_photo=True, has_caption=False)
    context = MockContext()

    chat_id = update1.message.chat.id
    processing_key = f"processing_{chat_id}"

    # Simular la lógica del bot
    def check_processing(update, context):
        message = update.message
        chat_id = message.chat.id
        message_id = message.message_id

        # Verificar si ya hay un procesamiento activo para este chat
        processing_key = f"processing_{chat_id}"
        if context.user_data.get(processing_key, False):
            logger.warning(f"🚫 Procesamiento ya activo para chat {chat_id} (mensaje {message_id}), ignorando posible duplicado")
            return False  # No procesar

        # Marcar que hay un procesamiento activo
        context.user_data[processing_key] = True
        logger.info(f"🔄 Iniciando procesamiento para chat {chat_id}, mensaje {message_id}")
        return True  # Procesar

    def cleanup_processing(context, chat_id):
        processing_key = f"processing_{chat_id}"
        context.user_data[processing_key] = False
        logger.info(f"✅ Procesamiento finalizado y flag limpiado para chat {chat_id}")

    # Primer mensaje - debería procesarse
    print("\n--- Primer mensaje ---")
    should_process_1 = check_processing(update1, context)
    print(f"¿Procesar mensaje 1?: {should_process_1}")
    print(f"Flag de procesamiento: {context.user_data.get(processing_key, False)}")

    # Segundo mensaje - debería ser ignorado
    print("\n--- Segundo mensaje (mismo chat) ---")
    should_process_2 = check_processing(update2, context)
    print(f"¿Procesar mensaje 2?: {should_process_2}")
    print(f"Flag de procesamiento: {context.user_data.get(processing_key, False)}")

    # Limpiar y probar de nuevo
    print("\n--- Limpiando procesamiento ---")
    cleanup_processing(context, chat_id)
    print(f"Flag después de limpieza: {context.user_data.get(processing_key, False)}")

    # Tercer mensaje - debería procesarse ahora
    print("\n--- Tercer mensaje (después de limpieza) ---")
    should_process_3 = check_processing(update1, context)
    print(f"¿Procesar mensaje 3?: {should_process_3}")
    print(f"Flag de procesamiento: {context.user_data.get(processing_key, False)}")

    print("\n=== Prueba completada ===")

if __name__ == "__main__":
    test_duplicate_prevention()

