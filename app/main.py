## _______________________________________________________________________________________
## En este archivo se define la aplicación principal de FastAPI.
## Se configuran el middleware de logging, CORS, y se incluyen los routers de los diferentes
## módulos (auth, chat, uploads). También se define un endpoint raíz de verificación.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat

# -----------------------------------------------------------------------------------------
# region             Configuración de logging
# -----------------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------------------
# region             Creación de la aplicación FastAPI
# -----------------------------------------------------------------------------------------

app = FastAPI(
    title="Asistente IA Normativas API",
    description="API Backend para el asistente de IA Normativas",
    version="1.0.0"
)

# -----------------------------------------------------------------------------------------
# region             Middleware de logging de solicitudes
# -----------------------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para registrar todas las solicitudes HTTP entrantes y su tiempo de procesamiento.
    """
    start_time = time.time()

    # Log de la solicitud entrante
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # Log del tiempo de procesamiento
    process_time = time.time() - start_time
    logger.info(f"Response: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")

    return response


# -----------------------------------------------------------------------------------------
# region             Configuración de CORS
# -----------------------------------------------------------------------------------------

origins = [
    "http://localhost:5173",
    "http://localhost:5000",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------------------
# region             Registro de routers
# -----------------------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
from app.api import uploads
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])

# -----------------------------------------------------------------------------------------
# region             Endpoint raíz de verificación
# -----------------------------------------------------------------------------------------

@app.get("/")
async def root():
    """Endpoint de verificación de estado."""
    return {"message": "Aistente IA Normativas API is running", "docs": "/docs"}