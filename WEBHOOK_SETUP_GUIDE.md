# 🚀 Guía de Configuración de Webhook para Railway

## ❌ Problema Identificado

El bot de Telegram no responde a comandos porque **la configuración del webhook en Railway es incorrecta**.

## 🔍 Diagnóstico del Problema

### Código Problemático Encontrado

En `fastapi_app.py`, había código que intentaba "inferir" la URL del webhook usando `RAILWAY_PROJECT_ID`:

```python
# ❌ CÓDIGO INCORRECTO (ya corregido)
railway_url = f"https://{os.getenv('RAILWAY_PROJECT_ID', 'unknown')}.up.railway.app"
```

**¿Por qué es incorrecto?**
- `RAILWAY_PROJECT_ID` es un UUID interno (ej: `e354271b-7d11-48c3-b0b4-7386f995c122`)
- No es el nombre del proyecto que aparece en la URL
- Genera URLs inválidas como `https://e354271b-7d11-48c3-b0b4-7386f995c122.up.railway.app`

## ✅ Solución Correcta

### 1. Obtener la URL Correcta de Railway

1. Ve a [Railway Dashboard](https://railway.app/dashboard)
2. Selecciona tu proyecto TELEWAN
3. Copia la URL del dominio (la que termina en `.up.railway.app`)

**Ejemplo de URL correcta:**
```
https://telewan-production.up.railway.app
```

### 2. Configurar Variables de Entorno

En Railway Dashboard → Tu Proyecto → Variables:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `WEBHOOK_URL` | `https://tu-proyecto.up.railway.app` | **OBLIGATORIO** - URL completa del webhook |
| `USE_WEBHOOK` | `true` | **OBLIGATORIO** - Forzar modo webhook |
| `TELEGRAM_BOT_TOKEN` | `tu_token_aquí` | **OBLIGATORIO** - Token del bot |
| `WAVESPEED_API_KEY` | `tu_api_key` | **OBLIGATORIO** - API key de WaveSpeed |

### 3. Verificar Configuración

Después de configurar las variables, **redeployea** la aplicación:

```bash
# Railway redeploy automático o manual
```

### 4. Diagnosticar el Estado

Ejecuta el diagnóstico incluido en el proyecto:

```bash
python fix_railway_webhook.py
```

O el diagnóstico completo:

```bash
python webhook_diagnostic.py
```

## 🔧 Scripts de Diagnóstico Disponibles

### `webhook_diagnostic.py`
- Verifica conectividad con Telegram
- Revisa configuración actual del webhook
- Prueba el endpoint `/health`
- Intenta configurar el webhook manualmente

### `fix_railway_webhook.py`
- Corrige automáticamente la configuración del webhook
- Verifica que la aplicación esté operativa
- Configura el webhook en Telegram

### `check_bot_status.py`
- Verificación completa del estado del bot
- Incluye diagnóstico de webhook

### `audit_bot_issues.py`
- Auditoría completa de todos los componentes
- Identifica problemas críticos

## 🚨 Errores Comunes y Soluciones

### ❌ Error: "WEBHOOK_URL requerida para Railway pero no configurada"

**Solución:** Configurar la variable `WEBHOOK_URL` en Railway Dashboard con la URL correcta.

### ❌ Error: "Webhook configurado pero no recibe mensajes"

**Causas posibles:**
1. URL incorrecta en `WEBHOOK_URL`
2. Puerto incorrecto (debe usar el asignado por Railway)
3. Firewall bloqueando conexiones
4. Token de bot inválido

**Solución:** Ejecutar `python webhook_diagnostic.py` para diagnóstico detallado.

### ❌ Error: "Aplicación no responde en /health"

**Causas posibles:**
1. Error en inicialización del bot
2. Puerto incorrecto
3. Variables de entorno faltantes

**Solución:** Revisar logs de Railway para errores de inicialización.

## 📋 Checklist de Verificación

- [ ] `WEBHOOK_URL` configurada correctamente en Railway
- [ ] `USE_WEBHOOK=true` configurado
- [ ] `TELEGRAM_BOT_TOKEN` válido
- [ ] `WAVESPEED_API_KEY` configurado
- [ ] Aplicación redeployeada en Railway
- [ ] Endpoint `/health` responde correctamente
- [ ] Webhook configurado en Telegram API
- [ ] Bot responde a comandos `/start`

## 🎯 Comandos para Probar

Después de la configuración correcta, prueba:

1. **Health check:**
   ```bash
   curl https://tu-proyecto.up.railway.app/health
   ```

2. **Enviar mensaje al bot:**
   - Busca tu bot en Telegram
   - Envía `/start`
   - Debería responder inmediatamente

3. **Verificar webhook:**
   ```bash
   python check_bot_status.py
   ```

## 📞 Soporte

Si después de seguir esta guía el bot aún no funciona:

1. Ejecuta `python webhook_diagnostic.py` y comparte la salida
2. Revisa los logs de Railway para errores
3. Verifica que todas las variables estén configuradas correctamente
4. Confirma que la URL del webhook sea accesible desde internet

---

**✅ Con esta configuración correcta, el bot debería funcionar perfectamente.**