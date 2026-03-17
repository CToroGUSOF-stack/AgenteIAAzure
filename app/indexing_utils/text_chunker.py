## _______________________________________________________________________________________
## En este archivo se definen funciones para dividir texto en chunks y crear documentos
## listos para indexar en Azure Search.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter


# -----------------------------------------------------------------------------------------
# region             Funciones de chunking
# -----------------------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Divide un texto en chunks usando un divisor recursivo.

    Args:
        text: Texto a dividir.
        chunk_size: Tamaño máximo de cada chunk.
        chunk_overlap: Superposición entre chunks.

    Returns:
        Lista de fragmentos de texto.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)

def create_chunk_docs(
    document_data: Dict[str, any],
    user_id: str,
    session_id: str,
    file_id: str,
    blob_url: str,
    created_at: str
) -> List[Dict[str, any]]:
    """
    Crea documentos (chunks) enriquecidos con metadatos para indexar.

    Args:
        document_data: Diccionario con 'content', 'filename', 'pages'.
        user_id: ID del usuario.
        session_id: ID de la sesión.
        file_id: ID del archivo.
        blob_url: URL del blob.
        created_at: Timestamp de creación.

    Returns:
        Lista de diccionarios, cada uno representando un chunk listo para indexar.
    """
    content = document_data.get("content", "")
    filename = document_data.get("filename", "")
    pages = document_data.get("pages", 1)

    chunks = chunk_text(content)

    docs = []

    for i, c_text in enumerate(chunks):
        docs.append({
            "id": f"{file_id}_chunk_{i}",
            "chunk_id": f"{file_id}_chunk_{i}",
            "content": c_text,
            "filename": filename,
            "blob_url": blob_url,
            "pages": pages,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "user_id": user_id,
            "session_id": session_id,
            "file_id": file_id,
            "created_at": created_at,
            "embedding": []
        })

    return docs
