## _______________________________________________________________________________________
## En este archivo se define el endpoint para la subida y procesamiento de documentos.
## 1. `/attachment`: Endpoint unificado que recibe archivos, extrae su texto,
##    genera chunks y embeddings, y los indexa en Azure Search.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import datetime
import logging
import io

from app.core.middleware import auth_manager, User
from app.core.utils import generate_id
from app.integrations.azure_blob_provider import blob_provider


# -----------------------------------------------------------------------------------------
# region                         Configuración inicial de servicios y esquemas
# -----------------------------------------------------------------------------------------

router = APIRouter()

class AttachmentResponse(BaseModel):
    """Modelo de respuesta para el endpoint /attachment."""
    message_id: str
    session_id: str
    text: str
    read_files: List[str]
    unread_files: List[str]


# -----------------------------------------------------------------------------------------
# region             Endpoint POST /attachment
# -----------------------------------------------------------------------------------------

@router.post("/attachment", response_model=AttachmentResponse)
async def upload_attachment(
    user_id: str = Form(...),
    session_id: str = Form(...),
    message: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    user: User = Depends(auth_manager)
):
    """
    Endpoint unificado para subir y procesar archivos.

    - Valida que el usuario autenticado coincida con `user_id`.
    - Procesa archivos según su tipo (PDF, Word, texto, imágenes) extrayendo texto.
    - Genera chunks, embeddings y los indexa en Azure Search.
    - Retorna lista de archivos leídos y no leídos.

    Tipos de archivo soportados:
    - PDF (application/pdf)
    - Texto plano (text/plain)
    - Word (application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    - Imágenes (image/jpeg, image/jpg, image/png, image/bmp, image/tiff)
    """
    try:
        # Validar que el usuario autenticado coincide
        if user.id != user_id:
            raise HTTPException(status_code=403, detail="No autorizado para acceder a los recursos de otro usuario")

        if not files:
            raise HTTPException(status_code=400, detail="Se requiere al menos un archivo.")

        # Tipos de archivo permitidos
        allowed_types = [
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg", "image/jpg", "image/png", "image/bmp", "image/tiff"
        ]

        read_files = []
        unread_files = []
        all_chunks = []

        for file in files:
            if file.content_type not in allowed_types:
                unread_files.append(file.filename)
                continue

            try:
                content = await file.read()

                # Procesar según tipo de archivo
                if file.content_type == "application/pdf":
                    # Usar Azure Document Intelligence
                    from app.integrations.azure_document_intelligence_provider import document_intelligence_provider
                    full_text = await document_intelligence_provider.analyze_document(content, file.filename)
                    doc_type = "pdf"
                    pages = max(1, len(full_text) // 3000)

                elif file.content_type in ["application/msword",
                                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                    # Procesar DOCX
                    from docx import Document
                    with io.BytesIO(content) as f:
                        doc = Document(f)
                        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                        full_text = "\n\n".join(paragraphs)
                    doc_type = "docx"
                    pages = max(1, len(full_text.split()) // 500)

                elif file.content_type == "text/plain":
                    # Texto plano
                    full_text = content.decode('utf-8', errors='ignore')
                    doc_type = "txt"
                    pages = 1

                elif file.content_type.startswith("image/"):
                    # Procesar imágenes con Document Intelligence
                    from app.integrations.azure_document_intelligence_provider import document_intelligence_provider
                    full_text = await document_intelligence_provider.analyze_document(content, file.filename)
                    doc_type = "image"
                    pages = 1

                else:
                    unread_files.append(file.filename)
                    continue

                # Crear metadata del documento
                file_id = f"file-{generate_id()}"
                blob_url = f"direct-upload://{user.id}/{session_id}/{file_id}/{file.filename}"
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

                # Crear chunks
                from app.indexing_utils.text_chunker import create_chunk_docs
                doc_data = {
                    "filename": file.filename,
                    "content": full_text,
                    "pages": pages,
                    "file_type": doc_type
                }

                chunks = create_chunk_docs(
                    document_data=doc_data,
                    user_id=user.id,
                    session_id=session_id,
                    file_id=file_id,
                    blob_url=blob_url,
                    created_at=now_str
                )

                # Generar embeddings
                from app.indexing_utils.embedding_generator import generate_embeddings
                chunks_with_embeddings = await generate_embeddings(chunks)

                # Indexar en Azure Search
                from app.indexing_utils.userdocs_uploader import upload_documents
                upload_documents(chunks_with_embeddings)

                read_files.append(file.filename)
                all_chunks.extend(chunks_with_embeddings)

                logging.info(f"Procesado {file.filename}: {len(chunks)} chunks")

            except Exception as e:
                logging.error(f"Error procesando {file.filename}: {e}")
                unread_files.append(file.filename)
                continue

        # Construir respuesta
        if message is None or message.strip() == "":
            message = "Describa el contenido de los archivos adjuntos proporcionados."

        # Crear un resumen del contenido procesado para el LLM
        content_summary = f"Archivos procesados: {', '.join(read_files)}\n"
        if all_chunks:
            sample_content = all_chunks[0].get("content", "")[:200] if all_chunks[0].get("content") else ""
            content_summary += f"Contenido extraído (ejemplo): {sample_content}..."

        return AttachmentResponse(
            message_id=generate_id(),
            session_id=session_id,
            text=f"Archivos procesados exitosamente. {len(read_files)} archivos fueron indexados. Puede preguntar sobre su contenido.",
            read_files=read_files,
            unread_files=unread_files
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en /attachment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
