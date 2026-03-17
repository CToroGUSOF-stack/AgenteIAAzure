<<<<<<< HEAD
﻿# Policía Nacional de Colombia - APPA-DHAA

![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Vue.js](https://img.shields.io/badge/vuejs-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D)
![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)

## 🤖 APPA-DHAA

**APPA-DHAA** es el asistente virtual de la **Policía Nacional de Colombia**, orientado al apoyo institucional en temas de **Derechos Humanos y Atención al Ciudadano**, con enfoque en el **Derecho Humano a la Alimentación Adecuada (DHAA)**.  

Este sistema implementa un patrón avanzado de **RAG (Retrieval-Augmented Generation)** para consultar documentos normativos, operativos y técnicos, fortaleciendo la toma de decisiones, la atención a la comunidad y la gestión del conocimiento institucional.


---

## Arquitectura

![Arquitectura del Sistema](./docs/architecture-diagram.png)

Más detalles en la documentación técnica:

---

## Características Principales

- **Arquitectura RAG Agéntica**: Utiliza modelos de Azure OpenAI combinados con Azure AI Search para proporcionar respuestas basadas en evidencia documental.
- **Análisis de Documentos en Tiempo Real**: Integración con **Azure Document Intelligence** para que los usuarios carguen y analicen sus propios archivos (PDF, DOCX, imágenes).
- **Persistencia de Sesiones**: Almacenamiento escalable en **Azure Cosmos DB** (SQL API) con gestión de historial de chat.
- **Seguridad Empresarial**: Autenticación integrada con **Microsoft Entra ID (Azure AD)** para control de acceso seguro.
- **Interfaz Intuitiva**: Frontend moderno construido con **Vue.js 3** y **Tailwind CSS**, optimizado para la visualización de referencias y fuentes.
- **Ingesta Automatizada**: Pipeline robusto de indexación para documentos oficiales de la Policía Nacional de Colombia.

---
## API y rutas principales

![API scheme](./docs/API.png)

---
## Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python 3.13)
- **IA/Orquestación**: LangChain, LangGraph, Azure OpenAI (GPT-4o/mini)
- **Búsqueda**: Azure AI Search (Vectores, HNSW, Búsqueda Semántica)
- **Seguridad**: MSAL, PyJWT (OAuth2 / Entra ID)
- **Base de Datos**: Azure Cosmos DB (NoSQL)

### Frontend
- **Framework**: Vue.js 3 (Vite)
- **Estilos**: Tailwind CSS 4.0, Vuetify
- **Comunicación**: Axios

### Infraestructura (Azure)
- **Hosting**: Azure Container Apps (Backend) y Azure Web Apps for Containers (Frontend).
- **Base de Datos**: Azure Cosmos DB (NoSQL).
- **Almacenamiento**: Azure Blob Storage (Documentos de usuario).
- **Registros**: Azure Container Registry (ACR).

---

## 📂 Estructura del Proyecto

- `app/`: Código fuente del Backend FastAPI.
  - `api/`: Endpoints de autenticación y chat.
  - `inference/`: Lógica del agente RAG y herramientas de búsqueda.
  - `integrations/`: Conectores para servicios de Azure (OpenAI, Search, Cosmos, Storage).
- `frontend/`: Aplicación SPA en Vue.js.
  - `src/components/chat/`: UI del chat y visualización de documentos.
- `indexing/`: Scripts para el procesamiento e indexación de documentos oficiales.

---

## Indexación de Documentos con Azure AI Search (indexing/)

Esta carpeta contiene una solución completa para procesar documentos (PDF y Word) y subirlos a **Azure AI Search** con embeddings vectoriales para búsquedas semánticas y RAG.

### Características principales 
- **Procesamiento de documentos**: Extracción de texto desde PDF y Word (.docx).
- **Chunking inteligente**: División en fragmentos con solapamiento para mejorar la recuperación.
- **Embeddings vectoriales**: Generación de embeddings mediante Azure OpenAI.
- **Gestión de índices**: Creación y administración de índices en Azure AI Search.
- **Subida por lotes**: Carga eficiente de documentos en lotes.
- **Manejo de errores**: Reportes y reintentos para operaciones fallidas.

### Primeros pasos - Quick Start

1) Instalar dependencias

```powershell
cd indexing
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Configurar el entorno

Copia `.env.example` a `.env` y configura tus credenciales de Azure (Azure OpenAI, Azure AI Search, etc.). Ejemplos:

```env
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_KEY=
AZURE_SEARCH_INDEX=
DOCUMENTS_PATH=./documents
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
BATCH_SIZE=100
```

3) Preparar documentos

Crea la carpeta `documents/`, o en cualquier ubicación local (pero poner el path en la variable `DOCUMENTS_PATH`) y coloca allí tus PDF y DOCX.

4) Ejecutar el script de indexación

```powershell
# Indexar y subir documentos
python main.py
# Reconstruir índice (elimina datos previos)
python main.py --recreate-index
# Procesar sin subir (para pruebas)
python main.py --skip-upload
```

### Estructura del módulo `indexing/` 🗂️

```
indexing/
├── main.py                      # Script principal
├── config.py                    # Gestión de configuración
├── document_processor.py        # Extrae texto de PDFs/Word
├── text_chunker.py              # Lógica de fragmentado
├── embedding_generator.py       # Genera embeddings con Azure OpenAI
├── search_index_manager.py      # Administra índices en Azure AI Search
├── document_uploader.py         # Subida en lotes a Azure AI Search
├── requirements.txt             # Dependencias
├── .env.example                 # Ejemplo de variables de entorno
└── documents/                   # Carpeta para tus documentos
```

### Opciones de configuración 🔧
- **CHUNK_SIZE**: Tamaño de cada fragmento (por defecto: 1000 caracteres)
- **CHUNK_OVERLAP**: Solapamiento entre fragmentos (por defecto: 200)
- **DOCUMENTS_PATH**: Ruta a los documentos (por defecto: `./documents`)
- **BATCH_SIZE**: Tamaño de lotes para subida (por defecto: 100)

### Esquema del índice 📐
El índice incluye campos como:
- `id`, `chunk_id`, `content`, `filename`, `filepath`, `blob_url`, `pages`, `file_type`, `chunk_index`, `total_chunks`, `embedding` (vector de 1536 dimensiones).

### Búsqueda vectorial
- **Algoritmo**: HNSW
- **Métrica**: Cosine
- **Dimensiones**: 1536 (embedding `text-embedding-ada-002`)
- **Campos semánticos**: `content` (contenido), `filename` (palabras clave)

### Ejemplos de uso
- Indexar todo: `python main.py`
- Reconstruir índice: `python main.py --recreate-index`
- Indexar archivos específicos: `python main.py --files "ruta/doc1.pdf" "ruta/doc2.docx"`

### Solución de problemas 🛠️
- "Configuration errors": Revisar `.env`
- "Documents path does not exist": Verificar `DOCUMENTS_PATH`
- Errores por límite de tasa: Reducir `BATCH_SIZE`
- Fallos en generación de embeddings: Verificar credenciales y deployment en Azure OpenAI
- Fallos de subida: Verificar que la clave de Azure AI Search tenga permisos admin

### Notas y recomendaciones
- Soporta PDF y DOCX
- Documentos grandes se fragmentan automáticamente
- Usa procesamiento por lotes y manejo de errores para escalabilidad

### Integración con el backend
Los documentos indexados están en el formato esperado por el backend y pueden ser consultados por el RAG chatbot (`app/tools/search_tool.py`).

### Dependencias principales
`azure-search-documents`, `azure-core`, `openai`, `langchain`, `langchain-openai`, `PyPDF2`, `python-docx`, `python-dotenv`.

### Notas importantes ⚠️
1. **Clave admin requerida**: Para crear índices y subir documentos se necesita la clave admin de Azure AI Search.
2. **Costos**: La generación de embeddings y el almacenamiento en Azure AI Search tienen costos asociados.
3. **Backup**: Respaldar índice antes de usar `--recreate-index`.
4. **Rutas**: Si usas Blob Storage, ajusta `blob_url` para referenciar archivos en la nube.

---

## ⚙️ Configuración del Entorno (.env)

El proyecto requiere un archivo `.env` en la raíz con las siguientes variables:
- `AZURE_AD_*`: Para la autenticación con Entra ID.
- `AZURE_OPENAI_*`: Para el modelo de chat y embeddings.
- `AZURE_SEARCH_*`: Para el índice de conocimientos.
- `AZURE_COSMOS_*`: Para la base de datos de sesiones.

---

## Ejecución Local

### Backend
1. Instalar dependencias: 

``` 
pip install -r requirements.txt
```

2. Ejecutar: 

``` 
uvicorn app.main:app --reload
```

O usando docker

```sh
docker build -t policia-backend .

```

Y luego ejecutamos el contenedor:

```sh

docker run --rm -it --env-file .env -p 8000:8000 policia-agent-backend:latest
```

### Frontend
1. Instalar dependencias: `cd frontend && npm install`
2. Ejecutar modo dev: `npm run dev`

O usando docker, nos vamos a la carpeta frontend y construimos la imagen y la ejecutamos:

```sh
cd frontend
docker build -t policia-agent-frontend:latest .
docker run -p 80:80 policia-agent-frontend:latest
```

Luego podemos acceder a la aplicación en `http://localhost`.

## 🚢 Despliegue en la Nube (Azure)

### 1. Construcción de Imágenes en ACR
```sh
az acr build --registry acrchatagenteastus2 --image policia-backend:latest .
az acr build --registry acrchatagenteastus2 --image policia-frontend:latest --build-arg VITE_API_URL=https://policia-aca-backend.azurecontainerapps.io/api ./frontend
```

---

## Diseño de Datos en Cosmos DB

### Particionamiento
El diseño garantiza alto rendimiento y escalabilidad:
1. **`session_container`** (PK: `/id`)
2. **`message_container`** (PK: `/session_id`)

---

## Soporte y Propiedad
Desarrollado por **DataKnow** para la **Policía Nacional de Colombia**.

=======
# AgenteIAAzure
Repositorio de codigo fuente del proyecto AgenteIAAzure pruebaPONAL
>>>>>>> 91b54d53c8fd88ea7d9c31c54fd5be8a3e227a26
