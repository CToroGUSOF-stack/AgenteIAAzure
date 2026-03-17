## _______________________________________________________________________________________
## En este archivo se definen funciones para extraer texto de diferentes tipos de archivos.
## Soporta: PDF, DOCX, imágenes (a través de Azure Document Intelligence), y texto plano.
## Incluye fallback a PyPDF2 para PDFs cuando Azure DI falla.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import io
import logging
from typing import Dict, Optional
import tempfile
import os

from docx import Document as DocxDocument

# Agregar PyPDF2 como fallback
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    logging.warning("PyPDF2 no está instalado, no habrá fallback para PDFs")


# -----------------------------------------------------------------------------------------
# region             Funciones de extracción de texto
# -----------------------------------------------------------------------------------------

async def extract_text(content: bytes, filename: str) -> Optional[Dict[str, any]]:
    """
    Extrae texto de un archivo a partir de sus bytes y nombre.

    Args:
        content: Contenido del archivo en bytes.
        filename: Nombre del archivo (para determinar extensión).

    Returns:
        Diccionario con 'filename', 'content', 'pages', 'file_type', o None si falla.
    """
    ext = filename.lower().split('.')[-1]

    if ext in ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']:
        try:
            return await extract_with_azure_di(content, filename, ext)
        except Exception as e:
            logging.warning(f"Azure DI failed for {filename}, trying fallback: {e}")
            if ext == 'pdf' and HAS_PYPDF2:
                return extract_text_from_pdf_fallback(content, filename)
            else:
                raise
    elif ext in ['docx', 'doc']:
        return extract_text_from_docx(content, filename)
    else:
        # Fallback para archivos de texto
        try:
            text = content.decode('utf-8', errors='ignore')
            return {
                "filename": filename,
                "content": text,
                "pages": 1,
                "file_type": "text"
            }
        except Exception:
            return None

async def extract_with_azure_di(content: bytes, filename: str, ext: str) -> Dict[str, any]:
    """
    Extrae texto usando Azure Document Intelligence.

    Args:
        content: Bytes del archivo.
        filename: Nombre del archivo.
        ext: Extensión del archivo.

    Returns:
        Diccionario con contenido extraído y metadatos.
    """
    try:
        from app.integrations.azure_document_intelligence_provider import document_intelligence_provider

        # DEBUG: Guardar el archivo temporalmente para diagnóstico
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        logging.info(f"Procesando {filename} con Azure DI, tamaño: {len(content)} bytes")

        full_text = await document_intelligence_provider.analyze_document(content, filename)

        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except:
            pass

        if not full_text or len(full_text.strip()) == 0:
            raise ValueError("Azure DI devolvió texto vacío")

        logging.info(f"Azure DI extrajo {len(full_text)} caracteres de {filename}")

        # Estimar páginas basado en contenido
        lines = full_text.count('\n') + 1
        num_pages = max(1, lines // 50)  # Aprox. 50 líneas por página

        return {
            "filename": filename,
            "content": full_text,
            "pages": num_pages,
            "file_type": ext
        }
    except Exception as e:
        logging.error(f"Error extrayendo con Azure DI {filename}: {e}")
        raise

def extract_text_from_pdf_fallback(content: bytes, filename: str) -> Dict[str, any]:
    """
    Fallback para PDFs usando PyPDF2 (y pdfminer si es necesario).

    Args:
        content: Bytes del PDF.
        filename: Nombre del archivo.

    Returns:
        Diccionario con contenido extraído y metadatos.
    """
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_parts = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text:
                text_parts.append(text)

        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            # Intentar con mejor extracción usando pdfminer
            from pdfminer.high_level import extract_text as extract_text_pdfminer
            pdf_file.seek(0)
            full_text = extract_text_pdfminer(pdf_file)

        return {
            "filename": filename,
            "content": full_text,
            "pages": len(pdf_reader.pages),
            "file_type": "pdf"
        }
    except Exception as e:
        logging.error(f"Error en fallback PyPDF2 para {filename}: {e}")
        raise

def extract_text_from_docx(content: bytes, filename: str) -> Dict[str, any]:
    """
    Extrae texto de un archivo DOCX.

    Args:
        content: Bytes del DOCX.
        filename: Nombre del archivo.

    Returns:
        Diccionario con contenido extraído y metadatos.
    """
    try:
        with io.BytesIO(content) as f:
            doc = DocxDocument(f)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paragraphs)

            # Estimar páginas
            words = len(full_text.split())
            estimated_pages = max(1, words // 500)

            return {
                "filename": filename,
                "content": full_text,
                "pages": estimated_pages,
                "file_type": "docx"
            }
    except Exception as e:
        logging.error(f"Error extrayendo DOCX {filename}: {e}")
        raise

