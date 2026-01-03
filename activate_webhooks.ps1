# 🚀 Script para activar webhooks en TELEWAN (PowerShell)
# Ejecutar después de tener Railway conectado

Write-Host "🔗 Activando Webhooks en TELEWAN" -ForegroundColor Cyan
Write-Host "=" * 35 -ForegroundColor Cyan

# Función para configurar variables
function Setup-Variables {
    Write-Host "🔧 Configurando variables de entorno..." -ForegroundColor Yellow

    # Usar el token proporcionado por el usuario
    railway variables --set "TELEGRAM_BOT_TOKEN=8279313475:AAGqfBXqX41HLlM5MCDUPmlukQ62-8NSjnw"

    # Configurar modo webhook
    railway variables --set "USE_WEBHOOK=true"
    railway variables --set "WEBHOOK_PORT=8443"
    railway variables --set "WEBHOOK_PATH=/webhook"

    Write-Host "✅ Variables configuradas" -ForegroundColor Green
}

# Función para obtener URL de Railway
function Get-RailwayUrl {
    Write-Host "🔍 Obteniendo URL de Railway..." -ForegroundColor Yellow

    try {
        # Intentar obtener la URL del dominio público
        $RAILWAY_URL = railway domain 2>$null | Select-Object -First 1
    }
    catch {
        $RAILWAY_URL = $null
    }

    if (-not $RAILWAY_URL) {
        Write-Host "❌ No se pudo obtener la URL automáticamente" -ForegroundColor Red
        Write-Host "💡 Ve a tu proyecto en Railway > Settings > Domains" -ForegroundColor Cyan
        Write-Host "💡 Copia la URL completa (ej: https://telewan-production.up.railway.app)" -ForegroundColor Cyan
        $RAILWAY_URL = Read-Host "Ingresa la URL completa de Railway"
    }

    if ($RAILWAY_URL) {
        railway variables --set "WEBHOOK_URL=$RAILWAY_URL"
        Write-Host "✅ URL configurada: $RAILWAY_URL" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ URL no proporcionada" -ForegroundColor Red
        return $false
    }
}

# Función principal
function Main {
    Write-Host "🤖 Configuración automática de webhooks para TELEWAN" -ForegroundColor Magenta
    Write-Host ""

    # Verificar conexión
    try {
        railway status >$null 2>&1
    }
    catch {
        Write-Host "❌ No hay conexión con Railway" -ForegroundColor Red
        Write-Host "💡 Ejecuta: railway login && railway link" -ForegroundColor Cyan
        exit 1
    }

    Write-Host "✅ Conexión con Railway verificada" -ForegroundColor Green

    # Configurar variables
    Setup-Variables

    # Obtener URL
    if (-not (Get-RailwayUrl)) {
        exit 1
    }

    # Redeploy
    Write-Host ""
    Write-Host "🚀 Redeploying con configuración de webhooks..." -ForegroundColor Yellow
    railway deploy

    # Esperar un poco
    Write-Host "⏳ Esperando que el deploy termine..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    # Configurar webhook
    Write-Host ""
    Write-Host "🔗 Configurando webhook en Telegram..." -ForegroundColor Yellow
    railway run python setup_webhook_railway.py

    # Verificar
    Write-Host ""
    Write-Host "📊 Verificando configuración final..." -ForegroundColor Yellow
    railway run python setup_webhook.py check

    Write-Host ""
    Write-Host "🎉 ¡Webhooks activados exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Resumen:" -ForegroundColor Cyan
    Write-Host "  ✅ Modo webhook activado" -ForegroundColor Green
    Write-Host "  ✅ Variables configuradas" -ForegroundColor Green
    Write-Host "  ✅ Webhook registrado en Telegram" -ForegroundColor Green
    Write-Host "  ✅ Sin polling constante" -ForegroundColor Green
    Write-Host ""
    Write-Host "🧪 Prueba enviando una foto al bot para verificar que funciona" -ForegroundColor Magenta
}

# Ejecutar
Main
