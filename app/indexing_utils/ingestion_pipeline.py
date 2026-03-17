## _______________________________________________________________________________________
## En este archivo se define el pipeline de ingestión de documentos.
## Orquesta la extracción, chunking, generación de embeddings y subida a Azure Search.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import logging
import datetime
from typing import Dict, Any, List

from app.core.utils import generate_id
from app.indexing_utils import (
    document_extractor,
    text_chunker,
    embedding_generator,
    userdocs_uploader
)

# -----------------------------------------------------------------------------------------
# region             Pipeline de ingestión
# -----------------------------------------------------------------------------------------

async def run_ingestion_pipeline(
    content: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    blob_url: str,
    file_id: str = None
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de ingestión para un archivo.

    Args:
        content: Contenido del archivo en bytes.
        filename: Nombre del archivo.
        user_id: ID del usuario.
        session_id: ID de la sesión.
        blob_url: URL del blob (para referencia).
        file_id: ID opcional del archivo; si no se provee, se genera uno nuevo.

    Returns:
        Diccionario con resultado de la operación:
            file_id: ID del archivo generado.
            chunks_count: Número de chunks creados.
            content_extracted: Texto extraído (para uso en prompt).
            message: Mensaje de estado.
    """
    try:
        # 1. Extract Text
        doc_data = await document_extractor.extract_text(content, filename)

        if not doc_data:
            logging.warning(f"Could not extract text from {filename}")
            return {
                "file_id": None,
                "chunks_count": 0,
                "message": "Could not extract text"
            }

        # 2. Chunking
        if not file_id:
            file_id = f"file-{generate_id()}"

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

        chunks = text_chunker.create_chunk_docs(
            document_data=doc_data,
            user_id=user_id,
            session_id=session_id,
            file_id=file_id,
            blob_url=blob_url,
            created_at=now_str
        )

        # 3. Embed
        chunks_with_embeddings = await embedding_generator.generate_embeddings(chunks)

        # 4. Upload to Search Index
        userdocs_uploader.upload_documents(chunks_with_embeddings)

        return {
            "file_id": file_id,
            "chunks_count": len(chunks),
            "content_extracted": doc_data["content"],  # Helpful for the Chat Prompt
            "message": "Success"
        }

    except Exception as e:
        logging.error(f"Error in ingestion pipeline for {filename}: {e}")
        raise

