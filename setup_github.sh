#!/bin/bash

# Script para configurar el repositorio en GitHub
# Reemplaza estas variables con tus valores reales:

GITHUB_USERNAME="tu_usuario_de_github"
REPO_NAME="telewan-bot"

# Una vez que hayas creado el repositorio en GitHub, ejecuta estos comandos:

echo "Ejecuta estos comandos después de crear el repositorio en GitHub:"
echo ""
echo "# Conectar el repositorio local con GitHub:"
echo "git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo ""
echo "# Hacer push del código:"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "# Verificar que todo esté correcto:"
echo "git remote -v"
echo "git status"

