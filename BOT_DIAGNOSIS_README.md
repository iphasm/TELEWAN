# 🔍 Diagnóstico del Bot de Telegram

## ❌ Problema: El bot no responde a comandos

Si el bot no responde en Telegram pero la aplicación funciona, sigue esta guía de diagnóstico paso a paso.

## 🚀 Diagnóstico Rápido

### En Railway (recomendado):
```bash
python live_bot_diagnosis.py
```

### Local (para desarrollo):
```bash
python comprehensive_bot_diagnosis.py
```

## 📋 Guía de Diagnóstico Paso a Paso

### Paso 1: Verificar Variables de Entorno
```bash
# En Railway Dashboard > Tu proyecto > Variables
TELEGRAM_BOT_TOKEN = [tu_token]
WEBHOOK_URL = https://tu-proyecto.up.railway.app
USE_WEBHOOK = true
```

### Paso 2: Verificar que la aplicación funciona
```bash
curl https://tu-proyecto.up.railway.app/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "components": {
    "telegram_bot": "operational"
  }
}
```

### Paso 3: Verificar webhook en Telegram
```bash
python test_bot_webhook.py
```

### Paso 4: Revisar logs en tiempo real
1. Ve a Railway Dashboard > Tu proyecto > Logs
2. Envía `/start` al bot en Telegram
3. Busca estos mensajes en los logs:

#### ✅ Mensajes que DEBERÍAS ver:
```
🔗 Webhook request received
📨 Webhook recibido: update_id=..., text='/start'..., user=...
✅ Enviando update ... a procesamiento
🔄 Procesando update ... 🔄
✅ Update ... procesado correctamente por telegram_app
🚀 START COMMAND RECEIVED
✅ START COMMAND PROCESSED SUCCESSFULLY
```

#### ❌ Si NO ves estos mensajes:

**Problema: Webhook no llega a la aplicación**
- Verificar que `WEBHOOK_URL` esté correcta
- Verificar que la aplicación esté ejecutándose
- Verificar que Railway puede acceder a la URL

**Problema: Webhook llega pero no se procesa**
- Buscar errores en los logs
- Verificar que el bot esté inicializado

**Problema: Mensaje procesado pero sin respuesta**
- El bot procesa pero no envía respuesta
- Verificar permisos del bot
- Buscar errores de red

## 🛠️ Scripts de Diagnóstico Disponibles

### `live_bot_diagnosis.py` (PRINCIPAL)
- Diagnóstico completo EN VIVO para Railway
- Verifica configuración, aplicación y webhook
- Ejecutar después de cada cambio

### `comprehensive_bot_diagnosis.py`
- Diagnóstico local completo
- Útil para desarrollo y testing

### `test_bot_webhook.py`
- Prueba específica del endpoint webhook
- Simula envío de actualizaciones

### `debug_bot_responses.py`
- Debugging detallado de respuestas
- Agrega logging extra a handlers

## 🔧 Soluciones Comunes

### ❌ "WEBHOOK_URL no configurada"
```bash
# En Railway Dashboard > Variables
WEBHOOK_URL = https://tu-proyecto.up.railway.app
```

### ❌ "Aplicación no saludable"
- Revisar logs de Railway para errores de inicialización
- Verificar que todas las dependencias estén instaladas

### ❌ "Webhook no configurado en Telegram"
```bash
python fix_railway_webhook.py
```

### ❌ "Mensajes pendientes"
- El bot no está procesando actualizaciones
- Revisar logs para errores en el procesamiento

## 📊 Estados Posibles

### ✅ TODO OK
- Health check: `healthy`
- Bot status: `operational`
- Webhook configurado correctamente
- Logs muestran procesamiento exitoso

### ⚠️ Aplicación OK, webhook mal configurado
- Health check: `healthy`
- Pero webhook URL incorrecta en Telegram
- Solución: `python fix_railway_webhook.py`

### ⚠️ Webhook OK, procesamiento fallido
- Webhook llega correctamente
- Pero error en `process_telegram_update`
- Revisar logs para errores específicos

### ❌ Configuración incompleta
- Variables faltantes
- Aplicación no inicia correctamente

## 🚨 Diagnóstico de Emergencia

Si nada funciona:

1. **Reset completo del webhook:**
   ```bash
   # En Telegram API manualmente
   curl "https://api.telegram.org/bot{TOKEN}/deleteWebhook"
   curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://tu-proyecto.up.railway.app/webhook"
   ```

2. **Redeploy completo:**
   - En Railway Dashboard > Settings > Redeploy

3. **Verificar token:**
   ```bash
   curl "https://api.telegram.org/bot{TOKEN}/getMe"
   ```

## 📞 Logs Específicos a Buscar

### Inicialización exitosa:
```
✅ Telegram Application inicializado
✅ Aplicación de Telegram registrada en app_state
✅ Webhook configurado correctamente
🚀 Iniciando servidor FastAPI
```

### Procesamiento de mensaje:
```
🔗 Webhook request received
📨 Webhook recibido: update_id=..., text='/start'
✅ Enviando update ... a procesamiento
🔄 Procesando update ...
✅ Update ... procesado correctamente
```

### Errores comunes:
```
❌ WEBHOOK_URL no configurada - REQUERIDA para Railway
❌ Aplicación de Telegram no inicializada
❌ Error procesando update
```

---

**🎯 Si sigues esta guía paso a paso, identificarás exactamente dónde está el problema.**