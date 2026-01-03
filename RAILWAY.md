# 🚂 Guía Completa de Despliegue en Railway

## Crear y Configurar el Volumen

### Paso 1: Crear Volumen desde Railway CLI

```bash
# Instalar Railway CLI (si no lo tienes)
npm install -g @railway/cli

# Login a tu cuenta
railway login

# Conectar al proyecto (desde el directorio del proyecto)
railway link

# Crear volumen
railway volume create telewan-storage

# Verificar que se creó
railway volume list
```

### Paso 2: Configurar Variables de Entorno

```bash
# Variables requeridas
railway variables set TELEGRAM_BOT_TOKEN=tu_token_de_telegram
railway variables set WAVESPEED_API_KEY=tu_api_key_de_wavespeed

# Variable opcional para volumen
railway variables set VOLUME_PATH=/app/storage
```

### Dirección del Volumen

En Railway, el volumen se monta automáticamente en:
```
/app/storage
```

Esta es la **ruta del volumen** dentro del contenedor. Si creas un archivo en `/app/storage/logs/bot.log`, persistirá entre despliegues.

## Despliegue Completo

```bash
# Desplegar la aplicación
railway deploy

# Ver logs
railway logs

# Verificar estado
railway status
```

## Configuración del Bot para Volumen

El bot está configurado para usar la variable `VOLUME_PATH` que puedes configurar en Railway. Por defecto usa `./storage`.

### Usos del Volumen:
- **Logs persistentes:** Guardar logs del bot entre reinicios
- **Cache:** Almacenar temporalmente archivos descargados
- **Configuración:** Archivos de configuración persistentes

## Troubleshooting

### Volumen no se monta
```bash
# Verificar variables
railway variables list

# Recrear volumen si es necesario
railway volume delete telewan-storage
railway volume create telewan-storage
```

### Error de permisos
Los volúmenes en Railway tienen permisos de escritura por defecto. Si hay problemas:

```bash
# Verificar desde el contenedor
railway run ls -la /app/storage
```

### Variables no se aplican
```bash
# Redeploy para aplicar cambios
railway deploy
```

## Costos

- **Volumen:** Se cobra por GB usado por hora
- **Aplicación:** Según uso de CPU/memoria
- **Transferencia:** Costos por ancho de banda

## Monitoreo

```bash
# Ver métricas
railway metrics

# Ver logs en tiempo real
railway logs --follow
```

¡El bot estará listo para usar una vez desplegado! 🤖✨

