## _______________________________________________________________________________________
## En este archivo se define una herramienta (tool) para realizar búsquedas de documentos
## utilizando el servicio Azure AI Search.
## La herramienta se integra con LangChain y utiliza embeddings de Azure OpenAI.
## _______________________________________________________________________________________

#-----------------------------------------------------------------------------------------
#region             Librerías
#-----------------------------------------------------------------------------------------

from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import tool

from app.integrations.azure_aisearch_provider import ai_search_provider
from app.integrations.azure_openai_provider import openai_provider

#-----------------------------------------------------------------------------------------
#region             Definición de la herramienta
#-----------------------------------------------------------------------------------------

@tool
def search(query: str, top_k: int = 3) -> dict:
    """método para realizar una búsqueda de documentos
    
    Args:
        query (str): string de consulta
        top_k (int, optional): número de resultados a devolver. Por defecto es 3.
    
    Returns:
        dict: resultados de búsqueda con nombre de archivo y blob_url
    """
    returns = []
    returns_str = ""
    try:
        # 1. Genera el embedding del query
        vector = openai_provider.model_embeddings.embed_query(query)
        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
            kind="vector",
            exhaustive=True
        )

        # 2. Realiza la búsqueda en Azure AI Search
        results = ai_search_provider.client.search(
            include_total_count=True,
            search_text=query,
            select=["filename", "content", "pages", "blob_url", "chunk_id", "page_start", "page_end", "pages_total", "section"],
            query_type="semantic",
            semantic_configuration_name="my-semantic-config",
            top=top_k,
            vector_queries=[vector_query]
        )

        # 3. Procesa y formatea los resultados
        for i, result in enumerate(results):
            doc = result
            filename = doc.get("filename", "N/A")
            blob_url = doc.get("blob_url", "N/A")
            content = doc.get("content", "N/A")
            page_number = doc.get("pages", "N/A")
            chunk_id = doc.get("chunk_id", "N/A")
            page_start = doc.get("page_start")
            page_end = doc.get("page_end")
            section = doc.get("section")

            returns.append({
                "filename": filename, 
                "blob_url": blob_url,
                "page_number": page_number,
                "page_start": page_start,
                "page_end": page_end,
                "section": section,
                "chunk_id": chunk_id,
                "snippet": content
            })

            # Construye el string formateado con filename + blob_url
            section_info = f" Section: {section}" if section else ""
            returns_str += f"[{i+1}]: Filename: {filename}{section_info} Page: {page_number} Content: {content}\n"

        response = {
            "results": returns,
            "results_str": returns_str
        }
    except Exception as e:
        # 4. Maneja la excepción en caso de error
        import logging
        logging.error(f"Search tool error: {str(e)}")
        response = {"results": [], "results_str": f"Error accessing search index: {str(e)}"}

    return response