# 🚀 Plan de Implementación: Bot Event-Driven

## 📋 Resumen Ejecutivo

Este documento describe el plan para transformar el bot TELEWAN de una arquitectura síncrona/bloqueante a una arquitectura **event-driven** completamente asíncrona.

---

## 🔍 Análisis de la Arquitectura Actual

### Estado Actual
```
┌─────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ACTUAL                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────┐     ┌─────────────┐     ┌────────────┐  │
│  │ Telegram  │────▶│   Flask/    │────▶│  Handler   │  │
│  │  Update   │     │  Polling    │     │  (sync)    │  │
│  └───────────┘     └─────────────┘     └─────┬──────┘  │
│                                              │         │
│                                              ▼         │
│                                    ┌─────────────────┐ │
│                                    │ time.sleep()   │ │
│                                    │ (BLOQUEANTE)   │ │
│                                    └─────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Problemas Identificados

| Problema | Impacto | Ubicación en Código |
|----------|---------|---------------------|
| **`time.sleep()` bloqueante** | Bloquea el event loop de asyncio | 8 ocurrencias en `bot.py` |
| **Requests síncronos** | No aprovecha async/await | `WavespeedAPI` usa `requests` |
| **Sin cola de tareas** | No puede escalar horizontalmente | Procesamiento en-línea |
| **Flask bloqueante** | No es async-native | `app.run()` es síncrono |
| **Polling manual de APIs** | Ineficiente y bloqueante | Generación de video |

---

## 🎯 Arquitectura Propuesta: Event-Driven

### Visión General
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA EVENT-DRIVEN PROPUESTA                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────┐     ┌─────────────┐     ┌────────────┐                  │
│  │ Telegram  │────▶│   Webhook   │────▶│   Event    │                  │
│  │  Update   │     │  (FastAPI)  │     │  Emitter   │                  │
│  └───────────┘     └─────────────┘     └─────┬──────┘                  │
│                                              │                          │
│                    ┌─────────────────────────┼────────────────────────┐ │
│                    │                         ▼                        │ │
│                    │        ┌─────────────────────────────┐           │ │
│                    │        │     Redis / Message Queue   │           │ │
│                    │        └─────────────────────────────┘           │ │
│                    │                    │                             │ │
│                    │    ┌───────────────┼───────────────┐             │ │
│                    │    ▼               ▼               ▼             │ │
│                    │ ┌──────┐      ┌──────┐      ┌──────────┐         │ │
│                    │ │Worker│      │Worker│      │Callback  │         │ │
│                    │ │  1   │      │  2   │      │ Handler  │         │ │
│                    │ └──────┘      └──────┘      └──────────┘         │ │
│                    │                                                   │ │
│                    └───────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes del Sistema Event-Driven

### 1. **Event Gateway (FastAPI + Starlette)**
```python
# Reemplaza Flask con FastAPI (async-native)
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()
    # Encolar evento para procesamiento asíncrono
    background_tasks.add_task(process_update, update)
    return {"status": "accepted"}
```

### 2. **Event Bus (Redis Pub/Sub o Celery)**
```python
# Opción A: Redis Pub/Sub para eventos simples
import aioredis

class EventBus:
    async def publish(self, event_type: str, data: dict):
        await self.redis.publish(f"events:{event_type}", json.dumps(data))
    
    async def subscribe(self, event_type: str, handler):
        channel = await self.redis.subscribe(f"events:{event_type}")
        async for message in channel.listen():
            await handler(json.loads(message))

# Opción B: Celery para tareas distribuidas
from celery import Celery

celery_app = Celery('telewan', broker='redis://localhost:6379')

@celery_app.task(bind=True, max_retries=3)
def process_video_generation(self, chat_id: int, image_url: str, prompt: str):
    # Procesamiento en background
    pass
```

### 3. **Async HTTP Client (aiohttp)**
```python
# Reemplaza requests con aiohttp
import aiohttp

class AsyncWavespeedAPI:
    async def generate_video(self, prompt: str, image_url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=payload) as response:
                return await response.json()
    
    async def poll_status(self, request_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.endpoint}/{request_id}") as response:
                return await response.json()
```

### 4. **Async Sleep (asyncio.sleep)**
```python
# Reemplaza time.sleep() con asyncio.sleep()
import asyncio

# ANTES (bloqueante)
time.sleep(0.5)

# DESPUÉS (no bloqueante)
await asyncio.sleep(0.5)
```

### 5. **Callback Handler (Webhooks de WaveSpeed)**
```python
# Endpoint para recibir callbacks de WaveSpeed cuando el video está listo
@app.post("/wavespeed/callback")
async def wavespeed_callback(request: Request):
    data = await request.json()
    
    if data['status'] == 'completed':
        await event_bus.publish('video_ready', {
            'request_id': data['id'],
            'video_url': data['outputs'][0]
        })
    
    return {"status": "received"}
```

---

## 🔄 Flujo de Eventos Propuesto

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO EVENT-DRIVEN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. USER SENDS IMAGE                                            │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │ Telegram Webhook │ ──▶ Event: "image_received"              │
│  └──────────────────┘                                          │
│                                                                 │
│  2. PROCESS IMAGE                                               │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │  Image Handler   │ ──▶ Event: "video_generation_started"    │
│  │  (async worker)  │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  3. CALL WAVESPEED API                                         │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │  Wavespeed API   │ ──▶ Returns request_id immediately       │
│  │  (async call)    │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  4. STORE PENDING TASK                                         │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │ Redis/Database   │ ──▶ Store: {request_id, chat_id, prompt} │
│  └──────────────────┘                                          │
│                                                                 │
│  5. WAVESPEED CALLBACK (or polling worker)                     │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │ Callback Handler │ ──▶ Event: "video_ready"                 │
│  └──────────────────┘                                          │
│                                                                 │
│  6. SEND VIDEO TO USER                                         │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────┐                                          │
│  │  Video Sender    │ ──▶ Event: "video_sent"                  │
│  │  (async worker)  │                                          │
│  └──────────────────┘                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de Archivos Propuesta

```
TELEWAN/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point (FastAPI + Uvicorn)
│   ├── config.py                  # Configuración
│   │
│   ├── events/                    # Sistema de eventos
│   │   ├── __init__.py
│   │   ├── bus.py                 # Event Bus (Redis Pub/Sub)
│   │   ├── types.py               # Tipos de eventos
│   │   └── handlers.py            # Event handlers
│   │
│   ├── api/                       # APIs externas (async)
│   │   ├── __init__.py
│   │   ├── wavespeed.py           # WaveSpeed API (aiohttp)
│   │   └── telegram.py            # Telegram Bot API helpers
│   │
│   ├── workers/                   # Background workers
│   │   ├── __init__.py
│   │   ├── video_generator.py     # Procesa generación de videos
│   │   ├── image_processor.py     # Procesa imágenes
│   │   └── optimizer.py           # Optimiza prompts
│   │
│   ├── handlers/                  # Command/Message handlers
│   │   ├── __init__.py
│   │   ├── commands.py            # /start, /help, etc.
│   │   ├── images.py              # Manejo de imágenes
│   │   └── callbacks.py           # Callback queries
│   │
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   ├── task.py                # Task model
│   │   └── user.py                # User preferences
│   │
│   └── storage/                   # Storage layer
│       ├── __init__.py
│       ├── redis_client.py        # Redis para colas y cache
│       └── file_storage.py        # Almacenamiento de archivos
│
├── docker-compose.yml             # Redis + App
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 🛠️ Fases de Implementación

### **Fase 1: Migración a Async I/O** ✅ COMPLETADA (2026-01-XX)
- [x] Reemplazar `requests` con `aiohttp`
- [x] Reemplazar `time.sleep()` con `asyncio.sleep()`
- [x] Refactorizar `WavespeedAPI` a `AsyncWavespeedAPI`
- [x] Agregar `aiohttp` a requirements.txt
- [x] Crear funciones async para optimización y generación de video
- [x] Implementar pruebas completas de funcionalidad async

```python
# requirements.txt additions
aiohttp>=3.9.0
aiofiles>=23.0.0
```

### **Fase 2: Migración a FastAPI** ✅ COMPLETADA (2026-01-XX)
- [x] Reemplazar Flask con FastAPI
- [x] Configurar Uvicorn como servidor ASGI
- [x] Migrar endpoint de webhook a FastAPI
- [x] Agregar BackgroundTasks para procesamiento inicial
- [x] Crear aplicación FastAPI completa con lifespan management
- [x] Implementar endpoints /health, /stats, /webhook
- [x] Configurar procesamiento async de updates con BackgroundTasks

```python
# requirements.txt additions
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

### **Fase 3: Sistema de Eventos** ✅ COMPLETADA (2026-01-XX)
- [x] Configurar Redis como message broker
- [x] Implementar EventBus con pub/sub
- [x] Crear tipos de eventos
- [x] Implementar event handlers
- [x] Crear 15 tipos de eventos específicos
- [x] Implementar handlers para eventos principales
- [x] Integrar con FastAPI lifespan management
- [x] Crear pruebas completas del sistema

```python
# requirements.txt additions
aioredis>=2.0.0
# o
redis>=5.0.0
```

### **Fase 4: Workers y Colas** (3-5 días)
- [ ] Implementar worker de generación de video
- [ ] Implementar worker de descarga/envío de video
- [ ] Configurar task queue (Celery o custom)
- [ ] Agregar reintentos automáticos

```python
# requirements.txt additions (opcional)
celery>=5.3.0
```

### **Fase 5: Callbacks y Webhooks** (2-3 días)
- [ ] Investigar si WaveSpeed soporta callbacks
- [ ] Implementar endpoint de callback
- [ ] Fallback a polling asíncrono si no hay callbacks
- [ ] Agregar deduplicación de eventos

### **Fase 6: Pruebas y Documentación** (2-3 días)
- [ ] Unit tests para cada componente
- [ ] Integration tests
- [ ] Load testing
- [ ] Documentación actualizada

---

## 📊 Comparación: Antes vs Después

| Aspecto | Arquitectura Actual | Arquitectura Event-Driven |
|---------|---------------------|---------------------------|
| **I/O** | Síncrono (requests) | Asíncrono (aiohttp) |
| **Sleep** | `time.sleep()` bloqueante | `asyncio.sleep()` no bloqueante |
| **Server** | Flask (WSGI sync) | FastAPI (ASGI async) |
| **Escalabilidad** | Single process | Multi-worker + Redis |
| **Concurrencia** | 1 tarea a la vez | Múltiples tareas paralelas |
| **Callbacks** | Polling manual | Webhooks + Event Bus |
| **Reintentos** | Código manual | Automático con backoff |
| **Monitoreo** | Logs básicos | Eventos trazables |

---

## 🎯 Beneficios Esperados

### **Rendimiento**
- ⚡ **10-50x más concurrencia** sin más recursos
- 🚀 **Respuesta inmediata** al usuario (no bloquea)
- 📉 **Menor uso de CPU** (no hay busy-waiting)

### **Escalabilidad**
- 📈 **Horizontal scaling** con múltiples workers
- 🔄 **Load balancing** automático con Redis
- 🌐 **Multi-región** posible

### **Mantenibilidad**
- 🧩 **Código modular** y testeable
- 📊 **Eventos trazables** para debugging
- 🔧 **Componentes independientes**

### **Resiliencia**
- 🔁 **Reintentos automáticos** con exponential backoff
- 💾 **Persistencia de tareas** en Redis
- 🛡️ **Aislamiento de fallos** entre workers

---

## 💻 Ejemplo de Código: Handler Event-Driven

```python
# src/handlers/images.py
from ..events import EventBus, ImageReceivedEvent, VideoGenerationStartedEvent
from ..api import AsyncWavespeedAPI

class ImageHandler:
    def __init__(self, event_bus: EventBus, wavespeed: AsyncWavespeedAPI):
        self.event_bus = event_bus
        self.wavespeed = wavespeed
    
    async def handle_image(self, update: dict):
        """Maneja imagen recibida - completamente asíncrono"""
        chat_id = update['message']['chat']['id']
        
        # 1. Respuesta inmediata al usuario
        await self.send_processing_message(chat_id)
        
        # 2. Obtener imagen
        image_url = await self.get_image_url(update)
        
        # 3. Iniciar generación (no esperar resultado)
        result = await self.wavespeed.generate_video(prompt, image_url)
        request_id = result['data']['id']
        
        # 4. Guardar tarea pendiente
        await self.save_pending_task(request_id, chat_id, prompt)
        
        # 5. Emitir evento para tracking
        await self.event_bus.publish(VideoGenerationStartedEvent(
            request_id=request_id,
            chat_id=chat_id
        ))
        
        # 6. El worker de polling se encargará del resto
        # O WaveSpeed llamará a nuestro callback cuando esté listo
```

---

## 🔧 Dependencias Actualizadas

```txt
# requirements.txt (Event-Driven)
python-telegram-bot==21.4
python-dotenv==1.0.0
pillow>=10.2.0

# Async HTTP
aiohttp>=3.9.0
aiofiles>=23.0.0

# Web Framework (ASGI)
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Message Queue / Cache
redis>=5.0.0

# Optional: Task Queue
# celery>=5.3.0

# Monitoring (opcional)
# prometheus-client>=0.19.0
```

---

## 🚀 Próximos Pasos

1. **Revisar y aprobar** este plan
2. **Crear branch** `feature/event-driven`
3. **Implementar Fase 1** (Async I/O)
4. **Probar en staging** antes de producción
5. **Desplegar incrementalmente**

---

## ❓ Preguntas Abiertas

1. **¿WaveSpeed soporta callbacks?** 
   - Si sí → Implementar webhook receiver
   - Si no → Implementar polling worker asíncrono

2. **¿Necesitas múltiples instancias del bot?**
   - Si sí → Celery + Redis es necesario
   - Si no → FastAPI BackgroundTasks puede ser suficiente

3. **¿Qué nivel de complejidad es aceptable?**
   - Mínimo: Async I/O + FastAPI
   - Medio: + Redis para colas
   - Máximo: + Celery para workers distribuidos

---

*Documento creado: Enero 2026*
*Autor: Asistente de IA*
*Versión: 1.0*

