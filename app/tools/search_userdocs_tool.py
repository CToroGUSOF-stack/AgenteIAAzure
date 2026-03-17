## _______________________________________________________________________________________
## En este archivo se define la herramienta de búsqueda en documentos subidos por el usuario.
## La herramienta consulta el índice de Azure Search específico para documentos de usuario
## (userdocs) y retorna los fragmentos más relevantes junto con metadatos.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import tool
from typing import Optional
import logging

from app.core import context
from app.indexing_utils.userdocs_uploader import get_user_search_client
from app.integrations.azure_openai_provider import openai_provider

from app.core.config import settings

# -----------------------------------------------------------------------------------------
# region             Herramienta search_userdocs
# -----------------------------------------------------------------------------------------

@tool
def search_userdocs(query: str, top_k: int = 3) -> dict:
    """
    Realiza una búsqueda en los documentos subidos por el usuario (PDFs, Word, etc.).
    Útil cuando la pregunta se refiere a "este documento", "el archivo adjunto", o información específica del usuario.

    Args:
        query: Texto de la consulta (puede ser "*" para listar todos los documentos).
        top_k: Número máximo de resultados a retornar.

    Returns:
        Diccionario con dos claves:
            - results: Lista de documentos encontrados con metadatos.
            - results_str: Representación textual formateada de los resultados.
    """
    print(f"🔍 DEBUG search_userdocs llamado con query: '{query}'")
    print(f"   top_k: {top_k}")

    returns = []
    returns_str = ""

    user_id = None
    session_id = None

    try:
        # 0. Check for wildcard/all-docs query
        is_wildcard = query.strip() == "*" or query.lower().strip() == "all"

        print(f"   ¿Es wildcard?: {is_wildcard}")

        vector_queries = []
        if not is_wildcard:
            # 1. Generate embedding only for specific queries
            print(f"   Generando embedding para query específica...")
            vector = openai_provider.model_embeddings.embed_query(query)
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=top_k,
                fields="embedding",
                kind="vector",
                exhaustive=True
            )
            vector_queries = [vector_query]

        # 2. Filter for isolation
        filter_expr = None

        print(f"   Usando filtro: {filter_expr}")

        # 3. Search
        client = get_user_search_client()
        print(f"   🔍 Buscando en índice: {settings.ai_services.azure_search_userdocs_index}")

        # Try a simple search first
        search_text = "*" if is_wildcard else query
        print(f"   search_text: '{search_text}'")

        # Try to filter by filename if the query looks like a filename
        filter_expr = None
        if query and (query.endswith('.pdf') or query.endswith('.docx') or query.endswith('.doc') or query.endswith('.txt')):
            filter_expr = f"search.ismatch('{query}', 'filename')"
            print(f"   🤔 Query parece nombre de archivo, usando filtro: {filter_expr}")

        results = client.search(
            include_total_count=True,
            search_text=search_text,
            filter=filter_expr,  # Try filtering by filename
            select=["filename", "content", "pages", "blob_url", "chunk_id", "user_id", "session_id", "id"],
            query_type="simple",  # Force simple for now
            top=top_k,
            vector_queries=vector_queries
        )

        # 4. Format results
        total_count = 0
        doc_count = 0

        for i, doc in enumerate(results):
            doc_count += 1
            if i == 0:
                total_count = doc.get("@search.total_count", 0)
                print(f"   📊 Total documents en índice: {total_count}")

            print(f"   📄 Documento {i+1} encontrado:")
            print(f"      ID: {doc.get('id', 'N/A')}")
            print(f"      Filename: {doc.get('filename', 'N/A')}")
            print(f"      User ID: {doc.get('user_id', 'N/A')}")
            print(f"      Session ID: {doc.get('session_id', 'N/A')}")
            print(f"      Content preview: {doc.get('content', 'N/A')[:100]}...")

            filename = doc.get("filename", "N/A")
            blob_url = doc.get("blob_url", "N/A")
            content = doc.get("content", "N/A")
            page_number = doc.get("pages", "N/A")
            chunk_id = doc.get("chunk_id", "N/A")
            doc_user_id = doc.get("user_id", "N/A")
            doc_session_id = doc.get("session_id", "N/A")

            returns.append({
                "filename": filename,
                "blob_url": blob_url,
                "page_number": page_number,
                "chunk_id": chunk_id,
                "snippet": content,
                "user_id": doc_user_id,
                "session_id": doc_session_id
            })

            returns_str += f"[{i+1}]: File: {filename}, User: {doc_user_id}, Session: {doc_session_id}, Content: {content[:200]}...\n"

        print(f"   ✅ Documentos encontrados en esta búsqueda: {doc_count}")

        response = {
            "results": returns,
            "results_str": returns_str if returns_str else "No se encontraron documentos en el índice."
        }

        logging.info(f"search_userdocs encontro {len(returns)} resultados")

    except Exception as e:
        print(f"   ❌ Error en search_userdocs: {e}")
        logging.error(f"Error in search_userdocs: {e}", exc_info=True)
        response = {"results": [], "results_str": f"Error searching user docs: {str(e)}"}

    return response
