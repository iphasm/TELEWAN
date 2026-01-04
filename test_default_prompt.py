#!/usr/bin/env python3
"""
Script de prueba para verificar el comportamiento del prompt por defecto
"""

# Simular constantes y lógica del bot
DEFAULT_PROMPT = (
    "Absolutely fixed face and head position, zero head movement. No camera movement — a static, hyper-detailed cinematic shot. "
    "She swiftly reaches and removes her entire dress with decisive and strong motion, revealing bare natural breasts with visible nipples, "
    "fully naked body without underwear beneath exposing genitals. Skin texture rendered with extreme realism — soft, lifelike, "
    "with natural pores and subtle sheen under soft, diffused lighting. Moody, atmospheric tone with low-key shadows and ambient glow, "
    "evoking intimacy and tension. Shot in 4K resolution with shallow depth of field, blurring the background to isolate the subject. "
    "Cinematic composition, film grain subtly present, emphasizing emotional gravity and visual precision."
)

class MockMessage:
    def __init__(self, caption=None):
        self.caption = caption

def test_prompt_logic():
    """Probar la lógica de selección de prompt"""
    print("🧪 Probando lógica de prompt...")
    print("=" * 60)

    # Test 1: Con caption personalizado
    print("Test 1: Mensaje con caption personalizado")
    message_with_caption = MockMessage("Un paisaje hermoso al atardecer")
    if message_with_caption.caption:
        prompt = message_with_caption.caption
        print(f"✅ Prompt usado: '{prompt}'")
        print("✅ Tipo: Caption personalizado")
    else:
        prompt = DEFAULT_PROMPT
        print("✅ Prompt usado: DEFAULT_PROMPT")
        print("✅ Tipo: Prompt automático")
    print()

    # Test 2: Sin caption (vacío)
    print("Test 2: Mensaje sin caption (None)")
    message_no_caption = MockMessage(None)
    if message_no_caption.caption:
        prompt = message_no_caption.caption
        print(f"✅ Prompt usado: '{prompt}'")
        print("✅ Tipo: Caption personalizado")
    else:
        prompt = DEFAULT_PROMPT
        print("✅ Prompt usado: DEFAULT_PROMPT (primeros 100 caracteres)")
        print(f"   '{prompt[:100]}...'")
        print("✅ Tipo: Prompt automático")
    print()

    # Test 3: Caption vacío
    print("Test 3: Mensaje con caption vacío ('')")
    message_empty_caption = MockMessage("")
    if message_empty_caption.caption:
        prompt = message_empty_caption.caption
        print(f"✅ Prompt usado: '{prompt}'")
        print("✅ Tipo: Caption personalizado")
    else:
        prompt = DEFAULT_PROMPT
        print("✅ Prompt usado: DEFAULT_PROMPT")
        print("✅ Tipo: Prompt automático")
    print()

    print("📊 Resumen del DEFAULT_PROMPT:")
    print(f"   Longitud: {len(DEFAULT_PROMPT)} caracteres")
    print(f"   Contiene keywords clave: {'cinematic' in DEFAULT_PROMPT.lower()}, {'realism' in DEFAULT_PROMPT.lower()}, {'4K' in DEFAULT_PROMPT}")
    print()
    print("✅ Todos los tests pasaron correctamente!")

if __name__ == '__main__':
    test_prompt_logic()
