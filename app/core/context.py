## _______________________________________________________________________________________
## En este archivo se definen variables de contexto para datos de ámbito de petición.
## Se utilizan para pasar el ID de usuario y sesión a herramientas que no aceptan argumentos.
## _______________________________________________________________________________________


# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from contextvars import ContextVar
from typing import Optional


# -----------------------------------------------------------------------------------------
# region             Variables de contexto
# -----------------------------------------------------------------------------------------

# Context variables
#session_context: ContextVar[Optional[str]] = ContextVar("session_context", default=None)
#user_context: ContextVar[Optional[str]] = ContextVar("user_context", default=None)

user_context: ContextVar[str] = ContextVar('user_context', default=None)
session_context: ContextVar[str] = ContextVar('session_context', default=None)


# -----------------------------------------------------------------------------------------
# region             Funciones auxiliares
# -----------------------------------------------------------------------------------------

def set_rag_context(user_id: str, session_id: str):
    """Helper para establecer las variables de contexto de usuario y sesión."""
    user_token = user_context.set(user_id)
    session_token = session_context.set(session_id)
    return user_token, session_token

def reset_rag_context(user_token, session_token):
    """Helper para restablecer las variables de contexto a su valor anterior."""
    user_context.reset(user_token)
    session_context.reset(session_token)
