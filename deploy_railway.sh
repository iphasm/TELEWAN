#!/bin/bash

# 🚀 Script de despliegue para Railway
# Ejecutar después de crear repositorio y volumen

echo "🚂 Configurando despliegue en Railway..."

# Paso 1: Conectar al proyecto
echo "📡 Conectando al proyecto..."
railway login
railway link

# Paso 2: Configurar variables de entorno
echo "🔧 Configurando variables de entorno..."
echo "Ingresa tu TELEGRAM_BOT_TOKEN (de @BotFather):"
read -s TELEGRAM_TOKEN
railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"

echo "Ingresa tu WAVESPEED_API_KEY:"
read -s WAVESPEED_KEY
railway variables set WAVESPEED_API_KEY="$WAVESPEED_KEY"

# Paso 3: Configurar volumen
echo "💾 Configurando volumen..."
railway variables set VOLUME_PATH=/app/storage

# Paso 4: Verificar configuración
echo "✅ Verificando configuración..."
railway variables list
railway volume list

# Paso 5: Desplegar
echo "🚀 Desplegando aplicación..."
railway deploy

# Paso 6: Verificar despliegue
echo "📊 Verificando despliegue..."
railway status
railway logs --follow



