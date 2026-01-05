# 🤖 Bot de Telegram - Foto a Video con IA

Un bot de Telegram que transforma fotografías en videos usando IA, específicamente el modelo **Wan 2.2 I2V 480p Ultra Fast** de Wavespeed.

## 🚀 Características

- 📸 **Transformación de fotos a videos**: Convierte imágenes estáticas en videos animados
- 🎬 **IA avanzada**: Usa múltiples modelos Wan 2.2 de Wavespeed (Ultra Fast, Fast, Quality, Text-to-Video)
- 🤖 **Optimización automática de prompts**: IA analiza tus captions y los mejora automáticamente para mejores resultados
- 📝 **Prompts inteligentes**: Utiliza el caption de la foto como descripción, con optimización automática opcional
- 🚫 **Prevención de duplicados**: Sistema inteligente que evita procesamiento múltiple del mismo mensaje
- ⚡ **Procesamiento ultra rápido**: Optimizado para respuestas rápidas con polling eficiente y robusto
- ⏱️ **Videos de 8 segundos**: Duración extendida para mejores resultados
- 💾 **Almacenamiento persistente**: Fotos y videos guardados en volumen con nombres únicos
- 🔄 **Soporte para forwards**: Procesa fotos forwardeadas que tengan captions descriptivos
- 🚫 **Negative prompt automática**: Filtros integrados para evitar elementos no deseados
- 🔒 **Seguro**: Manejo adecuado de archivos y configuración
- 🚫 **Prevención de duplicados**: Sistema inteligente que evita procesamiento múltiple del mismo mensaje
- 🛠️ **Manejo robusto de errores**: Logging detallado y validaciones exhaustivas para diagnóstico rápido
- 📥 **Descarga inteligente de videos**: Sistema de reintentos progresivos con manejo específico de errores de red
- 🔍 **Debugging avanzado**: Trazabilidad completa del procesamiento de mensajes para identificar problemas
- 🎯 **Múltiples formatos**: Soporta fotos, documentos de imagen y stickers estáticos

## 📋 Requisitos

- Python 3.8+
- Token de bot de Telegram (de @BotFather)
- API Key de Wavespeed

## 🛠️ Instalación

1. **Clona o descarga este repositorio**

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto con:
   ```env
   # Token del bot de Telegram (obtenlo de @BotFather)
   TELEGRAM_BOT_TOKEN=tu_token_aqui

# ID de usuario autorizado (opcional - si no se configura, permite a todos)
ALLOWED_USER_ID=tu_user_id_aqui

# API Key de Wavespeed
WAVESPEED_API_KEY=tu_api_key_aqui

# URL base de la API de Wavespeed (opcional)
WAVESPEED_BASE_URL=https://api.wavespeed.ai

# Modo Webhook (opcional - para mejor rendimiento)
USE_WEBHOOK=false  # true para usar webhooks, false para polling
WEBHOOK_URL=https://tu-proyecto.railway.app  # URL completa de Railway
WEBHOOK_PORT=8443  # Puerto del webhook
WEBHOOK_PATH=/webhook  # Ruta del endpoint
WEBHOOK_SECRET_TOKEN=tu_token_secreto  # Token opcional para seguridad
   ```

## 🚀 Uso

1. **Ejecuta el bot:**
   ```bash
   python bot.py
   ```

2. **En Telegram:**
   - Busca tu bot o usa el enlace directo
   - Envía `/start` para ver las instrucciones
   - Envía una foto con un caption descriptivo

## 📸 Cómo usar el bot

### 🎯 **Formatos de Imagen Soportados:**

El bot reconoce **múltiples formatos de imagen** usando verificación avanzada:

- **📷 Fotos directas**: Imágenes tomadas con la cámara o desde la galería
- **📄 Documentos de imagen**: Archivos JPG, PNG, WebP, GIF enviados como documentos
- **🎭 Stickers estáticos**: Stickers no animados (PNG/WebP)
- **🔄 Forwards**: Fotos forwardeadas de otros chats/canales

### 📝 **Pasos para usar:**

1. **Prepara tu imagen** en cualquiera de los formatos soportados
2. **Opcional: Agrega un caption descriptivo** (será el prompt para generar el video)
3. **Envía la imagen al bot**
4. **Espera** a que se procese (puede tomar 1-5 minutos)

### 🎬 **Prompt Automático:**

Si no proporcionas un caption, el bot usará automáticamente un **prompt cinematográfico predefinido** especializado en escenas íntimas y atmosféricas con movimiento dinámico y composición visual detallada.

**✅ Procesamiento completamente silencioso** sin mensajes explicativos ni notificaciones adicionales.

### 🔄 **Soporte para Forwards:**

El bot también procesa fotos que forwardees de otros chats o canales, siempre y cuando tengan un caption descriptivo. Simplemente forwardea la foto con su caption al bot y este la procesará igual que una foto enviada directamente.

**Nota**: Para forwards de fotos sin imagen adjunta, reenvía la imagen original con el caption incluido.

### 🎯 **Modelos de Wavespeed AI:**

El bot soporta múltiples modelos con diferentes características:

| Modelo | Resolución | Velocidad | Uso recomendado |
|--------|------------|-----------|-----------------|
| **Ultra Fast** | 480p | ⚡ Muy rápida | Previews y pruebas rápidas |
| **Fast** | 480p | 🚀 Rápida | Buen balance calidad/velocidad |
| **Quality** | 720p | 🎯 Alta calidad | Videos finales profesionales |
| **Text-to-Video** | 480p | ⚡ Muy rápida | Generación solo desde texto |

**Cambiar modelo:** Usa `/quality` para 720p, `/preview` para ultra rápido, o `/textvideo` para solo texto.

### 💡 **Captions Opcionales:**

**Opcional:** Puedes agregar un caption personalizado para controlar exactamente qué video se genera. Si no agregas caption, el bot usará un prompt automático cinematográfico.

**Ejemplos de captions efectivos:**
- "Un amanecer sobre las montañas con nubes moviéndose suavemente"
- "Una ciudad futurista con coches voladores y neones brillantes"
- "Un bosque mágico con hadas danzando entre los árboles"
- "Olas del océano rompiendo en la playa al atardecer"

**Sin caption:** Se usa automáticamente el prompt cinematográfico predefinido con escena íntima y composición visual detallada.

### 📹 **Videos Entregados:**

Cada video generado incluye como **caption el prompt completo** utilizado para crearlo:

- 🎬 **Prompt utilizado:** [texto completo del prompt]
- 🎨 **Prompt optimizado automáticamente** (si aplica)

Esto te permite ver exactamente qué prompt se usó, especialmente útil cuando se optimiza automáticamente o cuando usas el prompt por defecto.

### 🤖 **Optimización Automática de Prompts (Nueva API v3)**

El bot incluye **inteligencia artificial avanzada** usando la nueva API v3 de WaveSpeedAI para mejorar automáticamente tus captions.

**Parámetros de optimización:**
- **API**: Nueva WaveSpeedAI v3 Prompt Optimizer
- **Modo**: `video` (optimización específica para generación de video)
- **Estilo**: `default` (equilibrado para mejores resultados)

#### 🎯 **Cómo funciona:**
- **Análisis inteligente**: El bot analiza tu imagen y caption
- **Optimización contextual**: Usa tanto la imagen como tu texto original para generar prompts más precisos
- **Nueva API v3**: Utiliza el endpoint más reciente de WaveSpeedAI
- **Campo "text"**: Envía el caption del usuario directamente al optimizer
- **Procesamiento silencioso**: La optimización ocurre en segundo plano sin interrupciones
- **Manejo robusto de errores**: Si la optimización falla, continúa automáticamente con tu prompt original
- **Indicador sutil**: Solo muestra "🎨 Video con prompt optimizado" cuando se completa exitosamente
- **Mejor calidad**: Prompts optimizados generan videos de mejor calidad automáticamente

#### 📝 **Cuándo se optimiza:**
- ✅ Captions con texto descriptivo
- ✅ Cuando la optimización puede mejorar la calidad del video
- ✅ Activado manualmente con el comando `/optimize`

#### 🎨 **Ejemplos de optimización con nueva API:**

| **Tu Caption** | **Optimizado automáticamente** |
|---|---|
| "A woman, city walk, fashion" | "A beautiful woman walking confidently through a bustling city street, wearing stylish fashion, cinematic shot with dynamic camera movement, dramatic lighting, hyper-detailed, 4K resolution" |
| "sunset landscape" | "Breathtaking sunset landscape with vibrant orange and purple sky, majestic mountains silhouetted against the horizon, golden light casting long shadows, cinematic composition, atmospheric mood" |

#### ⚙️ **Control de optimización:**
- **Desactivado por defecto**: Para mantener control total sobre tus prompts
- **Comando `/optimize`**: Activa/desactiva la optimización automática
- **Configuración por usuario**: Cada usuario puede elegir su preferencia

#### 💡 **Tips para mejores resultados:**
- **Sé descriptivo**: Incluye detalles sobre movimiento, iluminación y estilo
- **Activa la optimización**: Usa `/optimize` para mejorar automáticamente tus captions
- **Combina ambos**: Usa captions detallados + optimización para resultados excepcionales
- **Prompt completo**: El bot muestra el prompt optimizado completo para tu revisión

### 🔍 **Verificación Múltiple de Imágenes**

El bot utiliza **4 métodos de detección** para asegurar que reconoce todo tipo de imágenes:

1. **📷 Detección de fotos**: Verifica arrays de fotos con múltiples resoluciones
2. **📄 Análisis de MIME types**: Identifica documentos que son imágenes (JPG, PNG, WebP, GIF)
3. **🎭 Validación de stickers**: Solo acepta stickers estáticos (no animados)
4. **🔄 Verificación de forwards**: Detecta intents de forward sin imagen adjunta

**Rechaza automáticamente:**
- ❌ Documentos no imagen (PDF, DOC, etc.)
- ❌ Stickers animados/WebP animados
- ❌ Mensajes sin imagen
- ❌ Forwards sin imagen adjunta

### 🚫 Negative Prompt Automática

El bot incluye automáticamente una negative prompt avanzada que filtra elementos no deseados como:
- Artefactos de calidad baja, distorsiones, deformaciones
- Texto, watermarks, logos, censuras
- Ropa, accesorios, elementos 3D/cartoon
- Movimientos estáticos, transiciones pobres, flickering

Esto asegura videos de mayor calidad sin necesidad de especificar estos filtros manualmente.

### 🛡️ Garantías de Entrega

El sistema incluye múltiples verificaciones para asegurar que los videos siempre se entreguen:

- **Polling robusto**: Verifica el estado cada 0.5 segundos hasta 2 minutos
- **Múltiples reintentos**: Hasta 5 intentos para obtener la URL del video
- **Validación de contenido**: Verifica que el video descargado tenga contenido válido
- **Reintentos de envío**: Múltiples intentos para enviar el video por Telegram
- **Logging detallado**: Registra todos los pasos para debugging
- **Mensajes informativos**: Notifica al usuario sobre el progreso y posibles issues

## 🔐 Autenticación de Usuarios

### Acceso Restringido (Opcional)

Para hacer el bot privado y que solo tú puedas usarlo:

1. **Obtén tu User ID:**
   - Envía un mensaje a [@userinfobot](https://t.me/userinfobot) en Telegram
   - Copia el ID que te da

2. **Configura la variable:**
   ```bash
   # Solo permite acceso a tu ID de usuario
   ALLOWED_USER_ID=123456789
   ```

3. **Resultado:**
   - ✅ Solo tú puedes usar el bot
   - ❌ Otros usuarios ven mensaje de "acceso denegado"

Si no configuras `ALLOWED_USER_ID`, el bot permite acceso a todos los usuarios.

## ⚙️ Configuración

### Variables de Entorno (Recomendado)

El bot se configura principalmente a través de variables de entorno:

#### Variables Obligatorias:
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram (obténlo de @BotFather)
- `WAVESPEED_API_KEY`: API Key de Wavespeed AI

#### Variables Opcionales:
- `ALLOWED_USER_ID`: ID de usuario autorizado (restringe acceso a un usuario específico)
- `DEFAULT_PROMPT`: Prompt por defecto cuando no se proporciona caption (ver ejemplo abajo)
- `DEFAULT_MODEL`: Modelo por defecto (`ultra_fast`, `fast`, `quality`, `text_to_video`)
- `USE_WEBHOOK`: Activar modo webhook (`true`/`false`)
- `WEBHOOK_URL`: URL del webhook para Railway/Heroku

#### Ejemplo de DEFAULT_PROMPT:
```
Absolutely fixed face and head position, zero head movement. No camera movement — a static, hyper-detailed cinematic shot. She swiftly reaches and removes her entire dress with decisive and strong motion, revealing bare natural breasts with visible nipples, fully naked body without underwear beneath exposing genitals. Skin texture rendered with extreme realism — soft, lifelike, with natural pores and subtle sheen under soft, diffused lighting. Moody, atmospheric tone with low-key shadows and ambient glow, evoking intimacy and tension. Shot in 4K resolution with shallow depth of field, blurring the background to isolate the subject. Cinematic composition, film grain subtly present, emphasizing emotional gravity and visual precision.
```

### Configuración en Código

El bot incluye configuración adicional personalizable en `config.py`:

- `MAX_VIDEO_DURATION`: Duración del video en segundos (default: 8)
- `ASPECT_RATIO`: Relación de aspecto del video (default: "16:9")
- `MAX_POLLING_ATTEMPTS`: Máximo número de intentos de polling (default: 240)
- `POLLING_INTERVAL`: Intervalo entre checks de estado en segundos (default: 0.5)
- `NEGATIVE_PROMPT`: Filtros automáticos para mejorar calidad (configurado)

## 🔧 Comandos disponibles

### 🤖 Comandos básicos:
- `/start` - Inicia el bot y muestra instrucciones
- `/help` - Muestra ayuda completa

### 🎬 Comandos de generación:
- `/models` - Lista todos los modelos disponibles de Wavespeed AI
- `/textvideo [prompt]` - Genera video solo desde texto (sin imagen)
- `/quality` - Activa modo 720p alta calidad para próximas imágenes
- `/preview` - Activa modo 480p ultra rápido para próximas imágenes
- `/optimize` - Activar/desactivar optimización automática de prompts con IA

## 📁 Estructura del proyecto

```
├── bot.py              # Código principal del bot
├── config.py           # Configuración y variables de entorno
├── requirements.txt    # Dependencias del proyecto
├── README.md          # Este archivo
└── .env               # Variables de entorno (crear manualmente)
```

## 🐛 Solución de problemas

### El bot no responde
- Verifica que el token de Telegram sea correcto
- Asegúrate de que el bot esté ejecutándose

### Error de API de Wavespeed
- Verifica tu API key de Wavespeed
- Comprueba que tengas créditos disponibles

### Videos no se generan
- Asegúrate de incluir un caption con la foto
- Prueba con captions más descriptivos
- Verifica la conexión a internet

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🚂 Despliegue en Railway

### ⚡ Modos de Operación

El bot soporta dos modos de operación:

#### 1. **Polling** (Modo por defecto - Fácil setup)
- El bot consulta periódicamente a Telegram por nuevas actualizaciones
- Más simple de configurar, pero menos eficiente
- Ideal para desarrollo y testing

#### 2. **Webhook** (Modo recomendado - Mejor rendimiento)
- Telegram envía actualizaciones directamente al bot
- Más eficiente y escalable
- Requiere configuración adicional pero elimina polling constante

### Si ya tienes repositorio y volumen creados:

1. **Conectar al proyecto:**
   ```bash
   railway login
   railway link
   ```

2. **Configurar variables de entorno:**
   ```bash
   railway variables set TELEGRAM_BOT_TOKEN=tu_token_aqui
   railway variables set WAVESPEED_API_KEY=tu_api_key_aqui
   railway variables set VOLUME_PATH=/app/storage
   ```

3. **Verificar configuración:**
   ```bash
   railway variables list
   railway volume list
   ```

4. **Desplegar:**
   ```bash
   railway deploy
   ```

5. **Verificar:**
   ```bash
   railway status
   railway logs --follow
   ```

### Configuración de Webhooks (Recomendado)

Para usar webhooks en lugar de polling (más eficiente):

#### 🚀 **Método Automático (Recomendado):**
```bash
# Hacer ejecutable el script
chmod +x railway_setup_webhook.sh

# Ejecutar configuración automática
./railway_setup_webhook.sh
```

El script te guiará paso a paso y configurará todo automáticamente.

#### 🔧 **Método Manual:**
1. **Configurar variables:**
   ```bash
   railway variables set USE_WEBHOOK=true
   railway variables set WEBHOOK_URL=https://tu-proyecto.railway.app
   railway variables set WEBHOOK_PORT=8443
   railway variables set WEBHOOK_PATH=/webhook
   ```

2. **Redeploy:**
   ```bash
   railway deploy
   ```

3. **Configurar Telegram:**
   ```bash
   # Automático:
   railway run python setup_webhook.py setup

   # Manual:
   curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://tu-proyecto.railway.app/webhook"
   ```

#### 🧪 **Testing Local:**
```bash
# Configurar entorno local
python test_webhook_local.py setup

# Probar configuración
python test_webhook_local.py test
```

#### 📊 **Verificación:**
```bash
# Verificar estado del webhook
railway run python setup_webhook.py check

# Ver logs
railway logs --follow
```

**Ventajas de Webhooks:**
- ✅ Respuestas instantáneas (sin polling cada 10s)
- ✅ Menos uso de CPU y ancho de banda
- ✅ Mejor escalabilidad
- ✅ Más eficiente para alta carga
- ✅ Mejor experiencia de usuario

### Configuración desde cero:

1. **Crear proyecto y conectar GitHub:**
   - Ve a Railway.app → "New Project"
   - Conecta tu repositorio GitHub

2. **Crear volumen:**
   ```bash
   railway volume create telewan-storage
   ```

3. **Seguir pasos 2-5 de arriba**

## 💾 Almacenamiento de Archivos

El bot guarda automáticamente todos los archivos en el volumen de Railway con nombres únicos en serie:

- **Fotos de entrada**: `input_YYYYMMDD_HHMMSS_XXXXXXX.jpg`
- **Videos generados**: `output_YYYYMMDD_HHMMSS_XXXXXXX.mp4`

### Ubicación:
```
/app/storage/
```

### Beneficios:
- ✅ **Historial persistente** entre despliegues
- ✅ **Nombres únicos** para evitar conflictos
- ✅ **Acceso rápido** a archivos procesados
- ✅ **Backup automático** en Railway

### Ruta del Volumen en Railway

Los volúmenes en Railway se montan automáticamente en:
```
/app/storage
```

Esta es la **dirección del volumen** que usarías para almacenamiento persistente.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Librería para bots de Telegram
- [Wavespeed AI](https://wavespeed.ai) - API de generación de videos con IA
- [Railway](https://railway.app) - Plataforma de despliegue

---

¡Disfruta creando videos increíbles con IA! 🎬✨
