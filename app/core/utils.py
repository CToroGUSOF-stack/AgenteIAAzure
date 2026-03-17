## _______________________________________________________________________________________
## En este archivo se definen funciones de utilidad general para la aplicación.
## Actualmente contiene un generador de IDs con timestamp y UUID.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from datetime import datetime
from pytz import timezone
import uuid


# -----------------------------------------------------------------------------------------
# region             Generador de IDs
# -----------------------------------------------------------------------------------------

def generate_id() -> str:
    """
    Genera un identificador único combinando un UUID abreviado y la marca de tiempo actual.

    Formato: UUID_corto-YYYYMMDDHHMMSS
    Ejemplo: 123e4567-e89b-12d3-a456-426614174000-20250324123045
    """
    now = datetime.now()
    str_now = now.strftime("%Y%m%d%H%M%S")                   # Formato: YYYYMMDDHHMMSS
    uuid_id = str(uuid.uuid4())
    short_uuid = '-'.join(uuid_id.split('-')[:-1])           # ID único sin el último segmento
    chat_id = f'{short_uuid}-{str_now}'
    return chat_id
