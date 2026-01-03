#!/bin/bash

# 🚀 Script para configurar webhooks en Railway
# Ejecutar después de tener el proyecto desplegado

echo "🔗 Configuración de Webhooks en Railway"
echo "======================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "setup_webhook.py" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio del proyecto TELEWAN"
    exit 1
fi

# Verificar Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado. Instálalo con: npm install -g @railway/cli"
    exit 1
fi

echo "📡 Verificando conexión con Railway..."
railway status > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ No hay conexión con Railway. Ejecuta: railway link"
    exit 1
fi

echo "✅ Conexión verificada"

# Solicitar información del usuario
echo ""
echo "Ingresa la información de tu proyecto:"

read -p "URL de Railway (ej: https://telewan-production.up.railway.app): " RAILWAY_URL
read -p "Token secreto del webhook (opcional, presiona Enter para omitir): " SECRET_TOKEN

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ URL de Railway es requerida"
    exit 1
fi

echo ""
echo "🔧 Configurando variables de entorno..."

# Configurar variables
railway variables set USE_WEBHOOK=true
railway variables set WEBHOOK_URL="$RAILWAY_URL"
railway variables set WEBHOOK_PORT=8443
railway variables set WEBHOOK_PATH=/webhook

if [ -n "$SECRET_TOKEN" ]; then
    railway variables set WEBHOOK_SECRET_TOKEN="$SECRET_TOKEN"
fi

echo "✅ Variables configuradas"

echo ""
echo "🚀 Redeploying con configuración de webhooks..."
railway deploy

echo ""
echo "⏳ Esperando que el deploy termine..."
sleep 10

echo ""
echo "🔗 Configurando webhook en Telegram..."
railway run python setup_webhook.py setup

echo ""
echo "📊 Verificando configuración..."
railway run python setup_webhook.py check

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📋 Resumen:"
echo "  - Webhooks activados"
echo "  - URL: $RAILWAY_URL/webhook"
echo "  - Puerto: 8443"
if [ -n "$SECRET_TOKEN" ]; then
    echo "  - Token secreto: Configurado"
fi

echo ""
echo "🧪 Prueba enviando un mensaje al bot para verificar que funciona"
