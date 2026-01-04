# 🚂 Configuración en Railway

## Volúmenes en Railway

En Railway, los volúmenes se montan automáticamente en rutas específicas dentro del contenedor. No tienen "direcciones" como direcciones IP, sino rutas de sistema de archivos.

### Crear un Volumen

1. **Desde el Dashboard:**
   - Ve a tu proyecto en Railway
   - Ve a la pestaña "Volumes"
   - Haz clic en "Create Volume"
   - Elige un nombre (ej: `telewan-storage`)
   - Se monta automáticamente en `/app/storage` o ruta especificada

2. **Desde Railway CLI:**
   ```bash
   railway volume create telewan-storage
   ```

### Ruta del Volumen

Por defecto, Railway monta los volúmenes en:
```
/app/storage
```

Esta es la **ruta del volumen** que usarías en tu aplicación.

### Configuración del Bot

Si quieres usar almacenamiento persistente para:
- Guardar logs
- Cache de imágenes/videos
- Base de datos temporal

Agrega esta configuración a tu servicio en Railway:

```bash
# Variable de entorno (opcional)
VOLUME_PATH=/app/storage
```

¿Para qué necesitas el volumen exactamente? ¿Logs, cache, o algo más específico?



