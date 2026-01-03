# 🤖 Bot de Telegram - Foto a Video con IA

Un bot de Telegram que transforma fotografías en videos usando IA, específicamente el modelo **Wan 2.2 480p Fast** de Wavespeed.

## 🚀 Características

- 📸 **Transformación de fotos a videos**: Convierte imágenes estáticas en videos animados
- 🎬 **IA avanzada**: Usa el modelo Wan 2.2 480p Fast de Wavespeed
- 📝 **Prompts personalizados**: Utiliza el caption de la foto como descripción para generar el video
- ⚡ **Procesamiento rápido**: Optimizado para respuestas rápidas
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

   # API Key de Wavespeed
   WAVESPEED_API_KEY=tu_api_key_aqui

   # URL base de la API de Wavespeed (opcional)
   WAVESPEED_BASE_URL=https://api.wavespeed.ai
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

1. **Toma o selecciona una foto**
2. **Agrega un caption descriptivo** (esto será el prompt para generar el video)
3. **Envía la foto al bot**
4. **Espera** a que se procese (puede tomar 1-5 minutos)

### 💡 Ejemplos de captions efectivos:

- "Un amanecer sobre las montañas con nubes moviéndose suavemente"
- "Una ciudad futurista con coches voladores y neones brillantes"
- "Un bosque mágico con hadas danzando entre los árboles"
- "Olas del océano rompiendo en la playa al atardecer"

## ⚙️ Configuración

El bot incluye configuración personalizable en `config.py`:

- `MAX_VIDEO_DURATION`: Duración del video en segundos (default: 5)
- `ASPECT_RATIO`: Relación de aspecto del video (default: "16:9")
- `MAX_POLLING_ATTEMPTS`: Máximo número de intentos de polling (default: 30)
- `POLLING_INTERVAL`: Intervalo entre checks de estado en segundos (default: 10)

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

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Librería para bots de Telegram
- [Wavespeed AI](https://wavespeed.ai) - API de generación de videos con IA

---

¡Disfruta creando videos increíbles con IA! 🎬✨
