# 🧪 Guía de Testing del Bot TELEWAN

## Verificar Estado del Despliegue

### 1. Conectar Railway CLI
```bash
railway link
# Selecciona tu proyecto TELEWAN
```

### 2. Verificar Estado
```bash
railway status
railway logs --tail 50
```

### 3. Verificar Variables
```bash
railway variables list
```

## Probar el Bot

### 1. Encontrar el Bot en Telegram
- Busca en Telegram: `@tu_bot_username`
- O usa el enlace directo que te dio @BotFather

### 2. Comandos Básicos
```
/start - Inicia el bot y muestra instrucciones
/help - Muestra ayuda y comandos disponibles
```

### 3. Probar Funcionalidad Principal
1. **Envía una foto** con un **caption descriptivo**
2. **Ejemplo de caption:**
   - "Un paisaje montañoso con nubes moviéndose suavemente"
   - "Una ciudad futurista con coches voladores"
   - "Olas del mar rompiendo en la playa al atardecer"

### 4. Verificar Respuesta
- El bot debería responder confirmando que recibió la imagen
- Después de procesar: debería enviar el video generado
- Tiempo aproximado: 30 segundos a 1 minuto

## Solución de Problemas

### ❌ Error: "No linked project found"
```bash
railway login
railway link
# Seleccionar proyecto TELEWAN
```

### ❌ Bot no responde
1. Verificar que el bot esté corriendo: `railway status`
2. Revisar logs: `railway logs --follow`
3. Verificar variables: `railway variables list`

### ❌ Error en generación de video
1. Verificar API key de WaveSpeed
2. Revisar logs del bot para errores específicos
3. Verificar que la imagen se recibió correctamente

### ❌ Error de volumen
```bash
railway volume list
# Debería mostrar "telewan-storage"
```

## Logs Útiles

### Ver logs en tiempo real
```bash
railway logs --follow
```

### Ver últimos 100 logs
```bash
railway logs --tail 100
```

### Buscar errores específicos
```bash
railway logs | grep -i error
```

## Métricas de Railway

### Ver uso de recursos
```bash
railway metrics
```

### Ver estado de servicios
```bash
railway services
```

## Checklist de Verificación ✅

- [ ] Railway CLI conectado: `railway link`
- [ ] Variables configuradas: `railway variables list`
- [ ] Volumen creado: `railway volume list`
- [ ] Bot desplegado: `railway status`
- [ ] Logs sin errores: `railway logs --tail 20`
- [ ] Bot responde a `/start` en Telegram
- [ ] Bot procesa fotos correctamente
- [ ] Videos se generan y envían

¡El bot debería estar funcionando correctamente! 🎉




