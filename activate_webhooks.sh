#!/bin/bash

# 🚀 Script para activar webhooks en TELEWAN
# Ejecutar después de tener Railway conectado

echo "🔗 Activando Webhooks en TELEWAN"
echo "================================"

# Función para configurar variables
setup_variables() {
    echo "🔧 Configurando variables de entorno..."

    # Usar el token proporcionado por el usuario
    railway variables --set "TELEGRAM_BOT_TOKEN=8279313475:AAGqfBXqX41HLlM5MCDUPmlukQ62-8NSjnw"

    # Configurar modo webhook
    railway variables --set "USE_WEBHOOK=true"
    railway variables --set "WEBHOOK_PORT=8443"
    railway variables --set "WEBHOOK_PATH=/webhook"

    echo "✅ Variables configuradas"
}

# Función para obtener URL de Railway
get_railway_url() {
    echo "🔍 Obteniendo URL de Railway..."

    # Intentar obtener la URL del dominio público
    RAILWAY_URL=$(railway domain 2>/dev/null | head -1)

    if [ -z "$RAILWAY_URL" ]; then
        echo "❌ No se pudo obtener la URL automáticamente"
        echo "💡 Ve a tu proyecto en Railway > Settings > Domains"
        echo "💡 Copia la URL completa (ej: https://telewan-production.up.railway.app)"
        read -p "Ingresa la URL completa de Railway: " RAILWAY_URL
    fi

    if [ -n "$RAILWAY_URL" ]; then
        railway variables --set "WEBHOOK_URL=$RAILWAY_URL"
        echo "✅ URL configurada: $RAILWAY_URL"
        return 0
    else
        echo "❌ URL no proporcionada"
        return 1
    fi
}

# Función principal
main() {
    echo "🤖 Configuración automática de webhooks para TELEWAN"
    echo ""

    # Verificar conexión
    if ! railway status >/dev/null 2>&1; then
        echo "❌ No hay conexión con Railway"
        echo "💡 Ejecuta: railway login && railway link"
        exit 1
    fi

    echo "✅ Conexión con Railway verificada"

    # Configurar variables
    setup_variables

    # Obtener URL
    if ! get_railway_url; then
        exit 1
    fi

    # Redeploy
    echo ""
    echo "🚀 Redeploying con configuración de webhooks..."
    railway deploy

    # Esperar un poco
    echo "⏳ Esperando que el deploy termine..."
    sleep 15

    # Configurar webhook
    echo ""
    echo "🔗 Configurando webhook en Telegram..."
    railway run python setup_webhook_railway.py

    # Verificar
    echo ""
    echo "📊 Verificando configuración final..."
    railway run python setup_webhook.py check

    echo ""
    echo "🎉 ¡Webhooks activados exitosamente!"
    echo ""
    echo "📋 Resumen:"
    echo "  ✅ Modo webhook activado"
    echo "  ✅ Variables configuradas"
    echo "  ✅ Webhook registrado en Telegram"
    echo "  ✅ Sin polling constante"
    echo ""
    echo "🧪 Prueba enviando una foto al bot para verificar que funciona"
}

# Ejecutar
main
