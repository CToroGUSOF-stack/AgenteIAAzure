## _______________________________________________________________________________________
## En este archivo se define la función para generar embeddings a partir de chunks de texto.
## Utiliza el proveedor de Azure OpenAI para obtener los vectores de embedding.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from typing import List, Dict
from app.integrations.azure_openai_provider import openai_provider


# -----------------------------------------------------------------------------------------
# region             Generación de embeddings
# -----------------------------------------------------------------------------------------

async def generate_embeddings(chunks: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Genera embeddings para una lista de chunks de texto y los añade a cada chunk.

    Args:
        chunks: Lista de diccionarios, cada uno debe contener una clave 'content' con el texto.

    Returns:
        La misma lista de chunks, con una nueva clave 'embedding' que contiene el vector.
    """
    texts = [chunk["content"] for chunk in chunks]
    if not texts:
        return chunks

    batch_size = 100  # Tamaño seguro por lote
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = await openai_provider.model_embeddings.aembed_documents(batch_texts)
        all_embeddings.extend(batch_embeddings)

    for chunk, emb in zip(chunks, all_embeddings):
        chunk["embedding"] = emb

    return chunks

