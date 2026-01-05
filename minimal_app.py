"""
Versión mínima de la aplicación para debugging Railway
"""
import os
import logging
from datetime import datetime

from fastapi import FastAPI
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TELEWAN Minimal")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "TELEWAN Bot Minimal",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting minimal app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

