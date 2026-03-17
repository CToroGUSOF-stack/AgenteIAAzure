## _______________________________________________________________________________________
## En este archivo se definen funciones para subir y eliminar documentos en el índice
## de Azure Search específico para documentos de usuario.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import json
from typing import List, Dict
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings


# -----------------------------------------------------------------------------------------
# region             Funciones de cliente y operaciones
# -----------------------------------------------------------------------------------------

def get_user_search_client() -> SearchClient:
    """
    Obtiene un cliente de búsqueda configurado para el índice de documentos de usuario.
    """
    return SearchClient(
        endpoint=settings.ai_services.azure_search_endpoint,
        index_name=settings.ai_services.azure_search_userdocs_index,
        credential=AzureKeyCredential(settings.ai_services.azure_search_key)
    )

def upload_documents(documents: List[Dict[str, any]]):
    """
    Sube una lista de documentos (chunks) al índice de Azure Search.

    Filtra campos que no existen en el índice y maneja el envío por lotes.

    Args:
        documents: Lista de diccionarios con los datos a indexar.
    """
    if not documents:
        print("No documents to upload")
        return

    client = get_user_search_client()

    # Filter out fields that don't exist in the index
    filtered_documents = []
    for doc in documents:
        # Create a new document with only the fields that exist in the index
        filtered_doc = {
            "id": doc.get("id"),
            "chunk_id": doc.get("chunk_id"),
            "filename": doc.get("filename"),
            "content": doc.get("content"),
            "embedding": doc.get("embedding", []),
            "user_id": doc.get("user_id"),
            "session_id": doc.get("session_id"),
            "file_id": doc.get("file_id"),
            "blob_url": doc.get("blob_url"),
            "pages": doc.get("pages"),
            "created_at": doc.get("created_at")
        }
        # Remove any None values
        filtered_doc = {k: v for k, v in filtered_doc.items() if v is not None}
        filtered_documents.append(filtered_doc)

    # Log el primer documento para ver la estructura
    if filtered_documents:
        print(f"First document keys after filtering: {list(filtered_documents[0].keys())}")
        print(f"Embedding dimension: {len(filtered_documents[0].get('embedding', []))}")

    batch_size = 1000

    for i in range(0, len(filtered_documents), batch_size):
        batch = filtered_documents[i:i + batch_size]
        try:
            results = client.upload_documents(documents=batch)

            # Log detallado de resultados
            succeeded = [r for r in results if r.succeeded]
            failed = [r for r in results if not r.succeeded]

            print(f"Batch {i//batch_size + 1}: {len(succeeded)} succeeded, {len(failed)} failed")

            if failed:
                for f in failed[:5]:  # Muestra solo los primeros 5 errores
                    print(f"Failed document error: {f.error_message}")

        except Exception as e:
            print(f"Error uploading batch to Azure Search: {e}")
            print(f"Error type: {type(e).__name__}")
            raise

def delete_documents_by_session(user_id: str, session_id: str):
    """
    Elimina todos los documentos asociados a una sesión del índice userdocs.

    Args:
        user_id: ID del usuario.
        session_id: ID de la sesión.
    """
    client = get_user_search_client()

    # Filter by user_id AND session_id
    filter_expr = f"user_id eq '{user_id}' and session_id eq '{session_id}'"

    try:
        results = client.search(search_text="*", filter=filter_expr, select=["id"])
        to_delete = [{"id": r["id"]} for r in results]

        while to_delete:
            batch = to_delete[:1000]
            to_delete = to_delete[1000:]
            client.delete_documents(documents=batch)

    except Exception as e:
        print(f"Error deleting documents for session {session_id}: {e}")
        raise
