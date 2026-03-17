## _______________________________________________________________________________________
## En este archivo se definen los esquemas Pydantic para las peticiones y respuestas HTTP
## de los diferentes endpoints de la API (chat, sesiones, archivos adjuntos, etc.).
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union



# -----------------------------------------------------------------------------------------
# region             Esquemas para chat
# -----------------------------------------------------------------------------------------

class CitationItem(BaseModel):
    """
    Representa una cita o referencia utilizada en la respuesta del asistente.
    Contiene información como índice, página, fragmento, URL y nombre del archivo.
    """
    index: int
    page: Optional[Union[str, int]] = None
    chunk: Optional[str] = None
    snippet: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None


class ResponseHTTPChat(BaseModel):
    """
    Respuesta del endpoint /message.
    Incluye el ID del mensaje, el texto de la respuesta y la lista de citas.
    """
    id: str = Field(..., alias="message_id", description="ID del mensaje generado")
    text: str = Field(..., description="Respuesta del modelo de IA")
    citations: List[CitationItem] = Field(default=[], description="Lista de referencias citadas")

    class Config:
        populate_by_name = True


class RequestHTTPChat(BaseModel):
    """
    Solicitud para el endpoint /message.
    Contiene el ID de sesión, la consulta del usuario y parámetros opcionales.
    """
    session_id: str = Field(..., description="ID de la sesión")
    session_name: Optional[str] = Field("Chat", description="Nombre de la sesión")
    query: str = Field(..., description="Consulta del usuario")
    flag_modifier: bool = Field(False, description="Modificador de comportamiento")
    model_name: str = Field("gpt-5-mini", description="Modelo de IA a usar (gpt-5-mini, gpt-4o, o1, o1-mini)")
    search_tool: bool = Field(True, description="Habilitar herramienta de búsqueda")



# -----------------------------------------------------------------------------------------
# region             Esquemas para sesiones
# -----------------------------------------------------------------------------------------

class RequestSessionCreate(BaseModel):
    """
    Solicitud para crear una nueva sesión.
    """
    user_id: str
    channel: str = "web"


class ResponseSession(BaseModel):
    """
    Respuesta al crear o consultar una sesión.
    """
    session_id: str



# -----------------------------------------------------------------------------------------
# region             Esquemas para listado de sesiones
# -----------------------------------------------------------------------------------------

class SessionItem(BaseModel):
    """
    Información resumida de una sesión para listados.
    """
    session_id: str
    session_name: str
    created_at: Optional[str] = None
    channel: Optional[str] = None


class ResponseHTTPSessions(BaseModel):
    """
    Respuesta con la lista de sesiones de un usuario.
    """
    sessions: List[SessionItem]



# -----------------------------------------------------------------------------------------
# region             Esquemas para obtener una sesión (con mensajes)
# -----------------------------------------------------------------------------------------

class MessageItem(BaseModel):
    """
    Representa un mensaje individual dentro de una sesión.
    Puede ser de rol 'user' o 'assistant' e incluye metadatos como fecha, valoración y citas.
    """
    id: str
    role: str  # "user" o "assistant"
    content: str
    created_at: Optional[str] = None
    rate: Optional[int] = None
    files: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[CitationItem]] = None


class ResponseHTTPOneSession(BaseModel):
    """
    Respuesta que contiene los detalles de una sesión específica y su lista de mensajes.
    """
    session_id: str
    session_name: str
    messages: List[MessageItem]



# -----------------------------------------------------------------------------------------
# region             Esquemas para eliminar sesión
# -----------------------------------------------------------------------------------------

class ResponseHTTPDelete(BaseModel):
    """
    Respuesta después de eliminar una sesión.
    Incluye un mensaje y el número de elementos eliminados.
    """
    message: str
    deleted_count: int



# -----------------------------------------------------------------------------------------
# region             Esquemas para attachment (archivos adjuntos)
# -----------------------------------------------------------------------------------------

class FileInfo(BaseModel):
    """
    Información de un archivo adjunto.
    """
    filename: str
    content_type: str
    size: int


class ResponseHTTPAttachment(BaseModel):
    """
    Respuesta del endpoint /attachment.
    Incluye el ID del mensaje generado, el texto de la respuesta y las citas.
    """
    id: str
    text: str
    citations: List[CitationItem] = Field(default=[], description="Lista de referencias citadas")



# -----------------------------------------------------------------------------------------
# region                         Esquemas para actualizar sesión
# -----------------------------------------------------------------------------------------

class RequestSessionUpdate(BaseModel):
    """
    Solicitud para actualizar el nombre de una sesión.
    """
    session_name: str = Field(..., description="Nuevo nombre de la sesión")


class ResponseSessionUpdate(BaseModel):
    """
    Respuesta después de actualizar el nombre de una sesión.
    """
    session_id: str
    session_name: str
    message: str

