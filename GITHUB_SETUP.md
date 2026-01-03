# 🚀 Configuración del Repositorio en GitHub

## Paso 1: Crear repositorio en GitHub

1. Ve a [GitHub.com](https://github.com) y haz login
2. Haz clic en el botón **"New repository"** (botón verde)
3. Configura el repositorio:
   - **Repository name**: `telewan-bot` (o el nombre que prefieras)
   - **Description**: `Bot de Telegram que transforma fotos en videos con IA usando Wavespeed`
   - **Visibility**: Public o Private (según prefieras)
   - ❌ **NO marques** "Add a README file" (ya tenemos uno)
   - ❌ **NO marques** "Add .gitignore" (ya tenemos uno)
   - ❌ **NO marques** "Choose a license" (por ahora)
4. Haz clic en **"Create repository"**

## Paso 2: Conectar el repositorio local

Una vez creado el repositorio, GitHub te mostrará comandos para conectar. Copia la URL del repositorio (termina en `.git`).

Ejecuta estos comandos en la terminal (reemplaza `TU_USUARIO` y `NOMBRE_DEL_REPO`):

```bash
# Conectar el repositorio local con GitHub
git remote add origin https://github.com/TU_USUARIO/NOMBRE_DEL_REPO.git

# Cambiar el nombre de la rama principal a 'main'
git branch -M main

# Hacer push del código
git push -u origin main
```

## Paso 3: Verificar la conexión

```bash
# Verificar que el remote esté configurado
git remote -v

# Ver el estado del repositorio
git status

# Ver el historial de commits
git log --oneline
```

## 🎯 Resumen de comandos

```bash
# 1. Agregar el repositorio remoto
git remote add origin https://github.com/TU_USUARIO/telewan-bot.git

# 2. Cambiar rama a main
git branch -M main

# 3. Push inicial
git push -u origin main

# 4. Verificar
git remote -v
git status
```

## 📝 Notas importantes

- El archivo `.env` **NO** se subirá a GitHub (está en `.gitignore`)
- Todas las credenciales sensibles están protegidas
- El repositorio incluye documentación completa en `README.md`

## 🆘 Solución de problemas

### Error: "fatal: remote origin already exists"
```bash
# Remover el remote existente y agregar el nuevo
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/NOMBRE_DEL_REPO.git
```

### Error: "Updates were rejected because the tip of your current branch is behind"
```bash
# Forzar push si es necesario (solo para el primer push)
git push -u origin main --force
```

¡Listo! Tu código estará en GitHub y podrás compartirlo o colaborar con otros. 🎉

