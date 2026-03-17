## _______________________________________________________________________________________
## En este archivo se definen los endpoints del chat de la API utilizando FastAPI:
## 1. `/message`: recibe una consulta del usuario y responde utilizando memoria contextual.
## 2. `/attachment`: permite subir archivos junto con un mensaje.
## 3. `/sessions`: obtiene todas las sesiones del usuario autenticado.
## Se hace uso de servicios como Azure AI Search
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File, Form
from typing import List, Optional
import logging

from app.inference.agent_rag import run_agent
from app.prompts.saludo import SALUDO
from app.schemas.handle_https import (
    RequestHTTPChat, ResponseHTTPChat,
    RequestSessionCreate, ResponseSession,
    ResponseHTTPSessions, ResponseHTTPOneSession,
    ResponseHTTPDelete, ResponseHTTPAttachment,
    RequestSessionUpdate, ResponseSessionUpdate
)
from app.core.utils import generate_id
from app.core.middleware import auth_manager, User
from app.core.config import settings

from datetime import datetime
import random
from app.integrations.azure_blob_provider import blob_provider
from app.core.middleware import AUTH_DISABLED, DEV_USER
from fastapi import Request
from app.inference.agent_rag import clear_session_history



# -----------------------------------------------------------------------------------------
# region             Configuración inicial de servicios
# -----------------------------------------------------------------------------------------

router = APIRouter()

# Tipos de archivo soportados para el endpoint de attachment
SUPPORTED_CONTENT_TYPES = [
    "application/pdf",
    "text/plain",
    "text/html",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/tiff"
]


# -----------------------------------------------------------------------------------------
# region             Endpoint POST /message
# -----------------------------------------------------------------------------------------

@router.post("/message", response_model=ResponseHTTPChat)
async def endpoint_message(
    request: RequestHTTPChat,
    user: User = Depends(auth_manager)
):
    """
    Envía un mensaje del usuario y recibe una respuesta generada por IA.

    - Requiere autenticación mediante token Bearer.
    - Utiliza el agente RAG para generar respuestas contextuales.
    - En modo sin Cosmos DB, no se verifica/crea la sesión en base de datos.
    """
    try:
        session_id = request.session_id

        # En modo sin Cosmos DB, no verificamos/creamos sesión
        # Solo pasamos la información al agente
        print(f"📝 Procesando mensaje para sesión: {session_id}, usuario: {user.id}")

        # Llamar a la función run_agent
        result = await run_agent(
            query=request.query,
            session_id=session_id,
            user_id=user.id
        )

        return ResponseHTTPChat(
            message_id=result.get("message_id", "N/A"),
            text=result["text"],
            citations=result.get("citations", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en /message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------------------
# region             Endpoint POST /attachment
# -----------------------------------------------------------------------------------------

@router.post("/attachment", response_model=ResponseHTTPAttachment)
async def upload_attachment(
    request: Request,
    message_id: str = "123",
    session_id: str = "123",
    session_name: str = Form("Chat", description="Nombre de la sesión"),
    message: str = "¿De qué trata el archivo?",
    files: List[UploadFile] = File(..., description="Archivos a procesar"),
    flag_modifier: bool = Form(False),
    model_name: str = Form("gpt-4o"),
    search_tool: bool = Form(True),
):
    """
    Sube archivos a AI Search para ser consultados.

    Tipos de archivo soportados:
    - PDF (.pdf)
    - Texto plano (.txt)
    - HTML (.html)
    - Word (.doc, .docx)
    - Excel (.xls, .xlsx)
    - PowerPoint (.ppt, .pptx)
    - Imágenes (.jpg, .png, .bmp, .tiff)

    El contenido se extrae según el tipo (Azure Document Intelligence para PDFs e imágenes,
    librerías nativas para Office, etc.), se divide en chunks, se generan embeddings
    y se indexan en Azure Search.
    """
    try:
        # Get user from request or use DEV_USER for testing
        try:
            user = await auth_manager(request, None)
        except Exception:
            from app.core.middleware import DEV_USER, AUTH_DISABLED
            if AUTH_DISABLED:
                user = DEV_USER
                print(f"🔧 Usando DEV_USER para tests: {user.id}")
            else:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

        import tempfile
        import os
        import datetime
        from app.core.utils import generate_id
        from app.indexing_utils.text_chunker import create_chunk_docs
        from app.indexing_utils.embedding_generator import generate_embeddings
        from app.indexing_utils.userdocs_uploader import upload_documents

        print(f"📎 Procesando {len(files)} archivos")
        print(f"   Usuario: {user.id}")
        print(f"   Sesión: {session_id}")

        # Validar tipos de archivo
        file_names = [file.filename for file in files]

        # Leer contenido de los archivos con EXTRACCIÓN DE TEXTO REAL
        files_content = []
        all_chunks = []  # Para acumular todos los chunks para indexación

        for file in files:
            content = await file.read()
            filename = file.filename
            file_extension = filename.lower().split('.')[-1] if '.' in filename else 'txt'

            print(f"   Extrayendo texto de {filename}...")

            # Extraer texto según el tipo de archivo
            if file_extension in ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                try:
                    # Usar Azure Document Intelligence
                    from app.integrations.azure_document_intelligence_provider import document_intelligence_provider
                    full_text = await document_intelligence_provider.analyze_document(content, filename)
                    doc_type = file_extension
                    pages = max(1, len(full_text) // 3000)
                    print(f"   ✅ {file_extension.upper()} extraído con Azure DI: {len(full_text)} caracteres")
                except Exception as e:
                    print(f"   ⚠️ Azure DI falló para {filename}, intentando PyPDF2: {e}")
                    if file_extension == 'pdf':
                        try:
                            import PyPDF2
                            from io import BytesIO
                            pdf_file = BytesIO(content)
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            text_parts = []
                            for page in pdf_reader.pages:
                                text = page.extract_text()
                                if text:
                                    text_parts.append(text)
                            full_text = "\n\n".join(text_parts)
                            doc_type = "pdf"
                            pages = len(pdf_reader.pages)
                            print(f"   ✅ PDF extraído con PyPDF2: {len(full_text)} caracteres, {pages} páginas")
                        except Exception as e2:
                            print(f"   ❌ PyPDF2 también falló: {e2}")
                            full_text = f"[Error extrayendo PDF: {str(e2)}]"
                            doc_type = "pdf"
                            pages = 1
                    else:
                        full_text = f"[No se pudo extraer texto de {filename}]"
                        doc_type = file_extension
                        pages = 1

            elif file_extension in ['docx', 'doc']:
                try:
                    import docx
                    from io import BytesIO
                    doc_file = BytesIO(content)
                    doc = docx.Document(doc_file)
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    full_text = "\n\n".join(paragraphs)
                    doc_type = "docx"
                    words = len(full_text.split())
                    pages = max(1, words // 500)
                    print(f"   ✅ DOCX extraído: {len(full_text)} caracteres, ~{pages} páginas")
                except Exception as e:
                    print(f"   ❌ Error extrayendo DOCX: {e}")
                    full_text = f"[Error extrayendo DOCX: {str(e)}]"
                    doc_type = "docx"
                    pages = 1

            else:
                # Archivos de texto
                try:
                    full_text = content.decode('utf-8', errors='ignore')
                    doc_type = file_extension
                    pages = 1
                    print(f"   ✅ Texto plano extraído: {len(full_text)} caracteres")
                except Exception as e:
                    print(f"   ❌ Error decodificando texto: {e}")
                    full_text = f"[Error decodificando archivo: {str(e)}]"
                    doc_type = file_extension
                    pages = 1

            # Guardar para el prompt (limitado)
            files_content.append({
                "filename": filename,
                "content": full_text[:15000]  # Limitar para no sobrecargar el prompt
            })

            # =========================================================
            # ¡¡¡INDEXAR EN AZURE SEARCH!!!
            # =========================================================
            try:
                if (full_text and len(full_text.strip()) > 100 and
                    not full_text.startswith('[') and
                    not full_text.startswith('Error')):

                    # Crear metadata para indexación
                    file_id = f"file-{generate_id()}"
                    blob_url = f"dev://{user.id}/{session_id}/{filename}"
                    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

                    print(f"   📝 PREPARANDO ÍNDEX para {filename}:")
                    print(f"      User ID en metadata: {user.id}")
                    print(f"      Session ID en metadata: {session_id}")
                    print(f"      File ID: {file_id}")

                    # Preparar datos del documento
                    doc_data = {
                        "filename": filename,
                        "content": full_text,
                        "pages": pages,
                        "file_type": doc_type
                    }

                    print(f"   📝 Creando chunks para {filename}...")
                    print(f"      Texto tamaño: {len(full_text)} caracteres")

                    # Crear chunks
                    chunks = create_chunk_docs(
                        document_data=doc_data,
                        user_id=user.id,
                        session_id=session_id,
                        file_id=file_id,
                        blob_url=blob_url,
                        created_at=now_str
                    )

                    print(f"   📊 Chunks creados: {len(chunks)}")

                    # Verificar la estructura de los chunks
                    if chunks:
                        first_chunk = chunks[0]
                        print(f"   📋 Estructura del primer chunk:")
                        for key, value in first_chunk.items():
                            if key != 'content':  # Skip full content
                                print(f"      {key}: {value}")
                        print(f"      Content preview: {first_chunk.get('content', '')[:100]}...")

                    # Generar embeddings
                    if chunks:
                        print(f"   🧠 Generando embeddings para {len(chunks)} chunks...")
                        chunks_with_embeddings = await generate_embeddings(chunks)

                        # Verificar que los embeddings se generaron
                        if chunks_with_embeddings and len(chunks_with_embeddings) > 0:
                            first_chunk = chunks_with_embeddings[0]
                            has_embedding = 'embedding' in first_chunk and len(first_chunk['embedding']) > 0
                            print(f"   ✅ Embeddings generados: {has_embedding}")
                            if has_embedding:
                                print(f"   🔢 Dimensión de embedding: {len(first_chunk['embedding'])}")
                        else:
                            print(f"   ❌ No se generaron embeddings")

                        all_chunks.extend(chunks_with_embeddings)
                    else:
                        print(f"   ⚠️ No hay chunks para generar embeddings")

            except Exception as e:
                print(f"   ❌ Error preparando chunks para {filename}: {e}")
                import traceback
                traceback.print_exc()

        # =========================================================
        # SUBIR TODOS LOS CHUNKS A AZURE SEARCH
        # =========================================================
        if all_chunks:
            try:
                print(f"📤 Subiendo {len(all_chunks)} chunks a Azure Search...")
                upload_documents(all_chunks)
                print(f"✅ {len(all_chunks)} chunks indexados en Azure Search")
            except Exception as e:
                print(f"❌ Error subiendo chunks a Azure Search: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ No hay chunks para indexar")

        # =========================================================
        # PRUEBA DIRECTA: Verificar índice después de subir
        # =========================================================
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential

            client = SearchClient(
                endpoint=settings.ai_services.azure_search_endpoint,
                index_name=settings.ai_services.azure_search_userdocs_index,
                credential=AzureKeyCredential(settings.ai_services.azure_search_key)
            )

            # Get document count
            count = client.get_document_count()
            print(f"📈 Conteo total en índice {settings.ai_services.azure_search_userdocs_index}: {count}")

            # Get a few documents - use SIMPLE search
            if count > 0:
                print("🔍 Buscando documentos con '*':")
                results = client.search(search_text="*", top=10, include_total_count=True)

                for i, doc in enumerate(results):
                    print(f"📄 Documento {i+1}:")
                    print(f"   ID: {doc.get('id', 'N/A')}")
                    print(f"   Filename: {doc.get('filename', 'N/A')}")
                    print(f"   User: {doc.get('user_id', 'N/A')}")
                    print(f"   Session: {doc.get('session_id', 'N/A')}")
                    print(f"   Content preview: {doc.get('content', 'N/A')[:100] if doc.get('content') else 'N/A'}")

                    # Check all fields
                    print(f"   All fields: {list(doc.keys())}")

            else:
                print("❌ El índice está vacío!")

            # Try a specific search for Coral.pdf
            print(f"\n🔍 Buscando específicamente 'Coral.pdf':")
            specific_results = client.search(
                search_text="Coral.pdf",
                filter="filename eq 'Coral.pdf'",  # Try exact match filter
                top=5,
                include_total_count=True
            )
            specific_count = 0
            for doc in specific_results:
                specific_count += 1
                print(f"✅ Encontrado: {doc.get('filename')}")
            print(f"   Resultados con filtro exacto: {specific_count}")

            # Try without filter
            print(f"\n🔍 Buscando 'Coral.pdf' sin filtro:")
            text_results = client.search(
                search_text="Coral.pdf",
                top=5,
                include_total_count=True
            )
            text_count = 0
            for doc in text_results:
                text_count += 1
                print(f"   Resultado {text_count}: {doc.get('filename')}")
            print(f"   Resultados con búsqueda de texto: {text_count}")

        except Exception as e:
            print(f"⚠️ Error verificando índice: {e}")
            import traceback
            traceback.print_exc()

        # Construir query que forze el uso de la herramienta
        # Instead of including the full content, just mention the files are indexed
        enriched_query = f"{message}\n\nHe subido estos archivos: {', '.join(file_names)} que han sido indexados. Por favor, utiliza la herramienta de búsqueda para consultar su contenido detallado cuando sea necesario para responder mi pregunta."

        # Optional: Include a small sample (not the full content) to give context
        # But not enough to answer the question without searching
        if files_content and len(files_content) > 0:
            # Include just a tiny sample (first 100 chars) to give context
            sample_content = files_content[0]['content'][:100] if files_content[0]['content'] else ""
            if sample_content and not sample_content.startswith('['):
                enriched_query += f"\n\nMuestra del contenido (primeros 100 caracteres del primer archivo): \"{sample_content}...\""

        print(f"📤 Query modificada para forzar uso de herramienta de búsqueda")
        print(f"   Archivos: {file_names}")

        # Llamar al agente
        result = await run_agent(
            query=enriched_query,
            session_id=session_id,
            user_id=user.id
        )

        return ResponseHTTPAttachment(
            id=message_id,
            text=result["text"],
            citations=result.get("citations", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en /attachment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------------------
# region             Endpoint PATCH /sessions/{session_id} (Rename)
# -----------------------------------------------------------------------------------------

@router.patch("/sessions/{session_id}", response_model=ResponseSessionUpdate)
async def update_session_name_endpoint(
    session_id: str,
    request: RequestSessionUpdate,
    user: User = Depends(auth_manager)
):
    """
    Actualiza el nombre de una sesión.

    En modo sin Cosmos DB, solo confirma la operación sin persistencia real.
    """
    try:
        # En modo sin Cosmos DB, solo confirmamos la operación
        return ResponseSessionUpdate(
            session_id=session_id,
            session_name=request.session_name,
            message="✅ Nombre actualizado correctamente (modo sin base de datos)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en /sessions/{session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------------------
# region             Endpoint GET /get_one_session
# -----------------------------------------------------------------------------------------

@router.get("/get_one_session", response_model=ResponseHTTPOneSession)
async def read_one_session(
    session_id: str = Query(..., description="ID de la sesión a obtener"),
    user: User = Depends(auth_manager)
):
    """
    Obtiene todos los mensajes de una sesión/conversación específica desde la memoria volátil.

    La memoria se mantiene en `session_histories` (diccionario en memoria).
    """
    try:
        from app.inference.agent_rag import session_histories
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        from datetime import datetime

        history = session_histories.get(session_id, [])
        messages_formatted = []

        # Recorremos el historial y construimos pares (usuario -> asistente)
        i = 0
        while i < len(history):
            msg = history[i]

            if isinstance(msg, HumanMessage):
                user_query = msg.content
                # Buscar el siguiente AIMessage (respuesta)
                ai_response = ""
                citations = []
                timestamp = datetime.now().isoformat()  # Podrías guardar timestamp real si lo necesitas

                # Avanzar hasta encontrar un AIMessage
                j = i + 1
                while j < len(history):
                    if isinstance(history[j], AIMessage):
                        ai_response = history[j].content
                        # Extraer citas de additional_kwargs
                        citations = history[j].additional_kwargs.get("citations", [])
                        break
                    j += 1

                # Crear el mensaje en el formato esperado
                messages_formatted.append({
                    "message_id": f"msg-{session_id}-{i}",
                    "session_id": session_id,
                    "user_query": user_query,
                    "ai_response": ai_response,
                    "tokens_in": 0,          # Si no se guardan, se pueden omitir o poner 0
                    "tokens_out": 0,
                    "citations": citations,
                    "timestamp": timestamp
                })

                i = j + 1  # Saltar el AIMessage ya procesado
            else:
                # Si encontramos un AIMessage sin HumanMessage previo (caso raro), lo saltamos
                i += 1

        # Si no hay mensajes, devolvemos array vacío
        return ResponseHTTPOneSession(
            session_id=session_id,
            session_name=f"💬 Sesión: {session_id}",
            messages=messages_formatted
        )

    except Exception as e:
        logging.error(f"Error en /get_one_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------------------
# region             Endpoint DELETE /delete_one_session/{session_id}
# -----------------------------------------------------------------------------------------

@router.delete("/delete_one_session/{session_id}", response_model=ResponseHTTPDelete)
async def delete_one_session(
    session_id: str = Path(..., description="ID de la sesión a eliminar"),
    user: User = Depends(auth_manager)
):
    """
    Elimina una sesión de la memoria volátil (session_histories).
    """
    try:
        # Limpiar memoria volátil
        clear_session_history(session_id)
        return ResponseHTTPDelete(
            message=f"🧹 Sesión '{session_id}' eliminada de la memoria.",
            deleted_count=1
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error en /delete_one_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------------------
# region             Endpoint POST /create_session (legacy)
# -----------------------------------------------------------------------------------------

@router.post("/create_session", response_model=ResponseSession)
async def create_session(request: RequestSessionCreate):
    """
    Crea una nueva sesión para un usuario.

    En modo sin Cosmos DB, genera un ID de sesión mock.
    """
    try:
        # En modo sin Cosmos DB, generamos un ID de sesión mock
        mock_session_id = f"dev-session-{generate_id()}"
        return ResponseSession(session_id=mock_session_id)

    except Exception as e:
        logging.error(f"Error en /create_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))