## _______________________________________________________________________________________
## En este archivo se define un proveedor simplificado para Azure Document Intelligence.
## Utiliza el modelo "prebuilt-read" para extraer texto de documentos e imágenes.
## Basado en implementaciones exitosas de otros proyectos.
## _______________________________________________________________________________________


# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import logging
from typing import List
from io import BytesIO

from azure.core.credentials import AzureKeyCredential
#from azure.ai.documentintelligence import DocumentAnalysisClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.exceptions import HttpResponseError

from app.core.config import settings



# -----------------------------------------------------------------------------------------
# region             Clase AzureDocumentIntelligence
# -----------------------------------------------------------------------------------------

class AzureDocumentIntelligence:
    """
    Servicio para analizar documentos usando Azure Document Intelligence.
    Versión simplificada usando el modelo "prebuilt-read".
    """

    def __init__(self):
        api_key = settings.ai_services.document_intelligence_key
        endpoint = settings.ai_services.document_intelligence_endpoint

        if not api_key or not endpoint:
            logging.warning("Document Intelligence credentials not configured")
            self.client = None
            return

        try:
            self.client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            logging.info("Document Intelligence client initialized")
        except Exception as e:
            logging.error(f"Error initializing Document Intelligence: {e}")
            self.client = None

    async def analyze_document(self, file_bytes: bytes, filename: str) -> str:
        """
        Analiza un documento usando el modelo "prebuilt-read" y retorna el texto extraído.

        Args:
            file_bytes: Contenido del archivo en bytes.
            filename: Nombre del archivo (solo para logging).

        Returns:
            Texto extraído del documento.
        """
        if not self.client:
            raise ValueError("Document Intelligence client not initialized")

        try:
            logging.info(f"Analyzing {filename}, size: {len(file_bytes)} bytes")

            # Usar BytesIO para el contenido
            file_obj = BytesIO(file_bytes)

            poller = self.client.begin_analyze_document(
                "prebuilt-read",
                document=file_obj
            )

            result = poller.result()

            # Extraer texto de cada página
            full_content_list = []
            for page in result.pages:
                page_text_lines = [line.content for line in page.lines]
                page_text = ' '.join(page_text_lines)
                full_content_list.append(page_text)

            full_text = '\n\n'.join(full_content_list)

            logging.info(f"Document analyzed: {len(full_content_list)} pages, {len(full_text)} chars")

            if len(full_text.strip()) == 0:
                logging.warning(f"No text extracted from {filename}")
                return ""

            return full_text

        except HttpResponseError as e:
            logging.error(f"HTTP error analyzing {filename}: {e}")
            raise RuntimeError(f"Error analyzing document: {e}")
        except Exception as e:
            logging.error(f"Unexpected error analyzing {filename}: {e}")
            raise



# -----------------------------------------------------------------------------------------
# region             Instancia global
# -----------------------------------------------------------------------------------------

document_intelligence_provider = AzureDocumentIntelligence()

