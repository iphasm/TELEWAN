# 🔧 Troubleshooting - Problemas Comunes

## Problemas con Railway CLI

### ❌ "No linked project found"
```bash
# Solución:
railway login
railway link
# Seleccionar proyecto TELEWAN de la lista
```

### ❌ "Command not found: railway"
```bash
# Instalar Railway CLI:
npm install -g @railway/cli

# Verificar instalación:
railway --version
```

## Problemas con Variables de Entorno

### ❌ Variables no aparecen
```bash
# Verificar:
railway variables list

# Si no aparecen, configurar:
railway variables set TELEGRAM_BOT_TOKEN=tu_token
railway variables set WAVESPEED_API_KEY=tu_api_key
railway variables set VOLUME_PATH=/app/storage
```

### ❌ Variables no se aplican al bot
```bash
# Redeploy después de cambiar variables:
railway deploy

# Verificar que se aplicaron:
railway logs --tail 20
```

## Problemas con el Bot

### ❌ Bot no responde en Telegram
```bash
# Verificar estado:
railway status

# Verificar logs:
railway logs --follow

# Posibles causas:
# 1. Token incorrecto
# 2. Bot no está corriendo
# 3. Error en el código
```

### ❌ Error al procesar imágenes
```bash
# Verificar logs específicos:
railway logs | grep -i "photo\|image\|error"

# Posibles causas:
# 1. Problema con URL de imagen de Telegram
# 2. API de WaveSpeed no disponible
# 3. Error en el payload
```

### ❌ Videos no se generan
```bash
# Verificar API key:
railway variables get WAVESPEED_API_KEY

# Verificar logs de WaveSpeed:
railway logs | grep -i "wavespeed\|video\|api"

# Posibles causas:
# 1. API key incorrecta
# 2. Créditos insuficientes
# 3. Error en el endpoint
```

## Problemas con Volumen

### ❌ Volumen no se monta
```bash
# Verificar volumen:
railway volume list

# Si no existe, crear:
railway volume create telewan-storage

# Verificar variable:
railway variables get VOLUME_PATH
```

### ❌ Error de permisos en volumen
```bash
# Verificar desde el contenedor:
railway run ls -la /app/storage

# El directorio debería tener permisos de escritura
```

## Problemas de Despliegue

### ❌ Despliegue falla
```bash
# Ver logs del despliegue:
railway logs --tail 100

# Comunes:
# 1. Dependencias faltantes en requirements.txt
# 2. Error de sintaxis en el código
# 3. Variables de entorno faltantes
```

### ❌ Build falla
```bash
# Ver logs detallados:
railway logs

# Posibles causas:
# 1. Python version incompatible
# 2. Dependencias rotas
# 3. Archivo faltante
```

## Problemas de Rendimiento

### ❌ Bot responde lento
```bash
# Ver métricas:
railway metrics

# Posibles causas:
# 1. Memoria insuficiente
# 2. CPU limitado
# 3. Conexión lenta a APIs externas
```

### ❌ Timeouts en generación de videos
```bash
# Verificar timeout actual (120 * 0.5s = 60s):
railway logs | grep -i "timeout\|attempt"

# Aumentar si es necesario modificando MAX_POLLING_ATTEMPTS
```

## Comandos Útiles para Debug

```bash
# Ver estado completo:
railway status

# Ver logs en tiempo real:
railway logs --follow

# Ejecutar comando en el contenedor:
railway run python --version

# Verificar conectividad:
railway run curl -I https://api.telegram.org

# Ver archivos del contenedor:
railway run ls -la /app/

# Ver uso de disco:
railway run df -h
```

## Contacto y Soporte

Si los problemas persisten:

1. **Railway Support**: https://help.railway.app/
2. **Telegram Bot API**: https://core.telegram.org/bots/api
3. **WaveSpeed AI**: Verificar estado de servicios

## Checklist de Debug

- [ ] Railway CLI instalado y conectado
- [ ] Variables de entorno configuradas
- [ ] Volumen creado y montado
- [ ] Despliegue exitoso
- [ ] Bot responde en Telegram
- [ ] Logs sin errores críticos
- [ ] Generación de videos funciona




