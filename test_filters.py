#!/usr/bin/env python3
"""
Script de prueba para los filtros de imagen
"""

# Simular las clases necesarias para testing
class MockDocument:
    def __init__(self, mime_type):
        self.mime_type = mime_type

class MockSticker:
    def __init__(self, is_animated):
        self.is_animated = is_animated

class MockPhotoSize:
    def __init__(self):
        self.file_id = "test"
        self.file_unique_id = "test"
        self.width = 100
        self.height = 100

class MockMessage:
    def __init__(self):
        self.photo = None
        self.document = None
        self.sticker = None

# Filtros a probar
def image_document_filter(message) -> bool:
    """Filtro para documentos que son imágenes"""
    if message.document:
        mime_type = message.document.mime_type
        if mime_type and mime_type.startswith('image/'):
            supported_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
            return mime_type.lower() in supported_formats
    return False

def static_sticker_filter(message) -> bool:
    """Filtro para stickers estáticos (no animados)"""
    if message.sticker:
        return not message.sticker.is_animated
    return False

def is_image_message(message) -> tuple[bool, str, str]:
    """
    Verifica si un mensaje contiene una imagen usando múltiples métodos de detección
    """
    # Método 1: Foto directa (photo array)
    if message.photo and len(message.photo) > 0:
        return True, "photo", ""

    # Método 2: Documento que es imagen (por MIME type)
    if message.document:
        mime_type = message.document.mime_type
        if mime_type and mime_type.startswith('image/'):
            # Tipos de imagen soportados
            supported_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
            if mime_type.lower() in supported_formats:
                return True, "document", ""
            else:
                return False, "", f"❌ Formato de imagen no soportado: {mime_type}.\n\n💡 **Formatos aceptados:** JPG, PNG, WebP, GIF"

    # Método 3: Sticker estático (no animado)
    if message.sticker and not message.sticker.is_animated:
        return True, "sticker", ""

    # Método 4: Verificar si es un forward de un mensaje con foto
    if hasattr(message, 'forward_origin') and message.forward_origin and hasattr(message.forward_origin, 'photo') and message.forward_origin.photo:
        # Es un forward de una foto, pero no tenemos acceso directo a la foto
        return False, "", "❌ Para forwards de fotos, reenvía la imagen con el caption incluido."

    # Si no se detectó ninguna imagen
    return False, "", (
        "❌ No se detectó ninguna imagen en tu mensaje.\n\n"
        "📸 **Formatos aceptados:**\n"
        "• Fotos (directamente desde la cámara/galería)\n"
        "• Documentos de imagen (JPG, PNG, WebP, GIF)\n"
        "• Stickers estáticos\n\n"
        "💡 Asegúrate de incluir un **caption descriptivo** con tu imagen."
    )

def test_filters():
    """Función de prueba para verificar los filtros de imagen"""
    print("🧪 Probando filtros de imagen...")
    print("=" * 50)

    # Test 1: Foto
    print("Test 1: Foto")
    photo_msg = MockMessage()
    photo_msg.photo = [MockPhotoSize()]
    result = is_image_message(photo_msg)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(photo_msg)}")
    print(f"  static_sticker_filter: {static_sticker_filter(photo_msg)}")
    print()

    # Test 2: Documento JPG
    print("Test 2: Documento JPG")
    doc_msg = MockMessage()
    doc_msg.document = MockDocument("image/jpeg")
    result = is_image_message(doc_msg)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(doc_msg)}")
    print(f"  static_sticker_filter: {static_sticker_filter(doc_msg)}")
    print()

    # Test 3: Documento PNG
    print("Test 3: Documento PNG")
    doc_msg2 = MockMessage()
    doc_msg2.document = MockDocument("image/png")
    result = is_image_message(doc_msg2)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(doc_msg2)}")
    print(f"  static_sticker_filter: {static_sticker_filter(doc_msg2)}")
    print()

    # Test 4: Documento PDF (no imagen)
    print("Test 4: Documento PDF")
    doc_msg3 = MockMessage()
    doc_msg3.document = MockDocument("application/pdf")
    result = is_image_message(doc_msg3)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(doc_msg3)}")
    print(f"  static_sticker_filter: {static_sticker_filter(doc_msg3)}")
    print()

    # Test 5: Sticker estático
    print("Test 5: Sticker estático")
    sticker_msg = MockMessage()
    sticker_msg.sticker = MockSticker(False)
    result = is_image_message(sticker_msg)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(sticker_msg)}")
    print(f"  static_sticker_filter: {static_sticker_filter(sticker_msg)}")
    print()

    # Test 6: Sticker animado
    print("Test 6: Sticker animado")
    sticker_msg2 = MockMessage()
    sticker_msg2.sticker = MockSticker(True)
    result = is_image_message(sticker_msg2)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(sticker_msg2)}")
    print(f"  static_sticker_filter: {static_sticker_filter(sticker_msg2)}")
    print()

    # Test 7: Mensaje vacío
    print("Test 7: Mensaje vacío")
    empty_msg = MockMessage()
    result = is_image_message(empty_msg)
    print(f"  is_image_message: {result}")
    print(f"  image_document_filter: {image_document_filter(empty_msg)}")
    print(f"  static_sticker_filter: {static_sticker_filter(empty_msg)}")
    print()

    print("✅ Pruebas completadas")

if __name__ == '__main__':
    test_filters()

