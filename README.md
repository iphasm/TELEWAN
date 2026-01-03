# 🤖 Bot de Telegram - Foto a Video con IA

Un bot de Telegram que transforma fotografías en videos usando IA, específicamente el modelo **Wan 2.2 I2V 480p Ultra Fast** de Wavespeed.

## 🚀 Características

- 📸 **Transformación de fotos a videos**: Convierte imágenes estáticas en videos animados
- 🎬 **IA avanzada**: Usa el modelo Wan 2.2 I2V 480p Ultra Fast de Wavespeed
- 📝 **Prompts personalizados**: Utiliza el caption de la foto como descripción para generar el video
- ⚡ **Procesamiento ultra rápido**: Optimizado para respuestas rápidas con polling eficiente y robusto
- ⏱️ **Videos de 8 segundos**: Duración extendida para mejores resultados
- 💾 **Almacenamiento persistente**: Fotos y videos guardados en volumen con nombres únicos
- 🔄 **Soporte para forwards**: Procesa fotos forwardeadas que tengan captions descriptivos
- 🚫 **Negative prompt automática**: Filtros integrados para evitar elementos no deseados
- 🔒 **Seguro**: Manejo adecuado de archivos y configuración

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

1. **Toma o selecciona una foto** (o forwardea una foto existente)
2. **Agrega un caption descriptivo** (esto será el prompt para generar el video)
3. **Envía la foto al bot**
4. **Espera** a que se procese (puede tomar 1-5 minutos)

### 🔄 **Soporte para Forwards:**

El bot también procesa fotos que forwardees de otros chats o canales, siempre y cuando tengan un caption descriptivo. Simplemente forwardea la foto con su caption al bot y este la procesará igual que una foto enviada directamente.

### 💡 Ejemplos de captions efectivos:

- "Un amanecer sobre las montañas con nubes moviéndose suavemente"
- "Una ciudad futurista con coches voladores y neones brillantes"
- "Un bosque mágico con hadas danzando entre los árboles"
- "Olas del océano rompiendo en la playa al atardecer"

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

El bot incluye configuración personalizable en `config.py`:

- `ALLOWED_USER_ID`: ID de usuario autorizado (opcional, permite acceso restringido)
- `MAX_VIDEO_DURATION`: Duración del video en segundos (default: 8)
- `ASPECT_RATIO`: Relación de aspecto del video (default: "16:9")
- `MAX_POLLING_ATTEMPTS`: Máximo número de intentos de polling (default: 240)
- `POLLING_INTERVAL`: Intervalo entre checks de estado en segundos (default: 0.5)
- `NEGATIVE_PROMPT`: Filtros automáticos para mejorar calidad (configurado)

## 🔧 Comandos disponibles

- `/start` - Inicia el bot y muestra instrucciones
- `/help` - Muestra ayuda y comandos disponibles

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

### Configuración de Webhooks (Opcional)

Para usar webhooks en lugar de polling (más eficiente):

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
   Una vez desplegado, configura el webhook en Telegram:
   ```bash
   curl "https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url=https://tu-proyecto.railway.app/webhook"
   ```

**Ventajas de Webhooks:**
- ✅ Respuestas instantáneas (sin polling)
- ✅ Menos uso de CPU y ancho de banda
- ✅ Mejor escalabilidad
- ✅ Más eficiente para alta carga

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
