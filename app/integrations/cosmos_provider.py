## _______________________________________________________________________________________
## En este archivo se define una clase para interactuar con Azure Cosmos DB.
## Proporciona métodos asíncronos para gestionar la persistencia de las conversaciones,
## incluyendo la creación, almacenamiento y recuperación de sesiones y mensajes.
## _______________________________________________________________________________________

#-----------------------------------------------------------------------------------------
#region             Librerías
#-----------------------------------------------------------------------------------------

from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from typing import List
import logging

from app.core.utils import current_colombian_time
from app.core.config import settings

#-----------------------------------------------------------------------------------------
#region             Clase Cosmos DB
#-----------------------------------------------------------------------------------------

class AzureCosmosDB:
    """
    Clase que encapsula la lógica para interactuar con Azure Cosmos DB.
    Gestiona la conexión y las operaciones CRUD para sesiones y mensajes.
    """
    def __init__(self):
        # Obtiene las configuraciones desde el objeto de configuración global
        self.endpoint = settings.cosmos_db.azure_cosmos_endpoint
        self.key = settings.cosmos_db.azure_cosmos_key
        self.database_name = settings.cosmos_db.azure_cosmos_database_name
        self.container_sessions = settings.cosmos_db.azure_cosmos_session_container_name
        self.container_messages = settings.cosmos_db.azure_cosmos_message_container_name

        try:
            # Inicializa el cliente y los clientes de la base de datos y los contenedores
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            self.sessions_container = self.database.get_container_client(self.container_sessions)
            self.messages_container = self.database.get_container_client(self.container_messages)
        except exceptions.CosmosHttpResponseError as e:
            # Captura y registra errores de conexión
            logging.error(f"Error de conexión a Cosmos DB: {str(e)}")
            raise

    #-----------------------------------------------------------------------------------------
    #region             gestión de sesiones
    #-----------------------------------------------------------------------------------------

    async def session_exists(self, session_id: str) -> bool:
        """Verifica si una sesión existe en el contenedor de sesiones."""
        try:
            await self.sessions_container.read_item(
                item=session_id,
                partition_key=session_id
            )
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False

    async def create_session(self, session_data: dict):
        """Crea un nuevo documento de sesión en Cosmos DB."""
        document = {
            "id": session_data["session_id"],
            "user_id": session_data["user_id"],
            "modelo_ia":settings.ai_services.model_ia_name,
            "version_api_ia":settings.ai_services.openai_api_version,
            "message": [],
            "fecha_creacion": current_colombian_time(),
            "name_session": session_data.get("name_session", f"Chat {current_colombian_time()}"),
            "channel": session_data.get("channel", "web"),
            "user_email": session_data.get("user_email")
        }
        return await self.sessions_container.create_item(document)

    #-----------------------------------------------------------------------------------------
    #region             gestión de mensajes
    #-----------------------------------------------------------------------------------------

    async def save_message(self, message_data: dict):
        """Guarda un mensaje y actualiza la sesión con una referencia a este."""
        doc_message = {
            "id": message_data["message_id"],
            "session_id": message_data["session_id"],
            "ia_response": message_data["ai_response"],
            "user_query": message_data.get("user_query", ""), # Allow empty/missing for system/greeting messages
            "tokens_in": message_data.get("tokens_in", 0),
            "tokens_out": message_data.get("tokens_out", 0),
            "created_at": current_colombian_time(),
            "citations": message_data.get("citations", [])
        }
        # If user_query is missing, maybe it's a Greeting?
        # But 'user_query' key matches schema in 'save_message'.
        # The code above uses message_data["user_question"] which would fail if missing.
        # Let's fix that key access to be safe or map it correctly.
        # Original code was: "user_query": message_data["user_question"]
        # I will change it to use .get with default "" to allow system messages
        await self.messages_container.create_item(doc_message)

        # Nota: Ya no actualizamos la sesión con la lista de mensajes.
        # Al usar partition_key="/session_id" en mensajes, podemos consultarlos eficientemente
        # con get_session_messages sin necesidad de mantener una lista de IDs en la sesión.

    async def get_session_messages(self, session_id: str) -> List[dict]:
        """Obtiene los mensajes de una sesión, limitados por la configuración."""
        limit = settings.ai_services.message_memory_limit
        if limit <= 0:
            return []
        else:
            query = f"""
                SELECT c.ia_response, c.user_query, c.user_question FROM c
                WHERE c.session_id = @session_id
                ORDER BY c.created_at DESC
                OFFSET 0 LIMIT {limit}
            """
        params = [{"name": "@session_id", "value": session_id}]

        items = []
        async for item in self.messages_container.query_items(
            query=query,
            parameters=params,
            partition_key=session_id
        ):
            # Normalize user_query if it was saved as user_question
            if "user_question" in item and not item.get("user_query"):
                item["user_query"] = item["user_question"]
            items.append(item)

        return items

    async def update_rate(self, message_id: str, session_id: str, new_rate: bool):
        """Actualiza la valoración (rate) de un mensaje específico."""
        doc = await self.messages_container.read_item(
            item=message_id,
            partition_key=session_id
        )
        doc["rate"] = new_rate
        # Use the full document in replace_item to avoid passing 'partition_key' as a kwarg
        # which can be forwarded incorrectly to the underlying HTTP client.
        await self.messages_container.replace_item(
            item=doc,
            body=doc
        )

    async def update_session_name(self, session_id: str, new_name: str):
        """Actualiza el nombre de una sesión."""
        doc = await self.sessions_container.read_item(
            item=session_id,
            partition_key=session_id
        )
        doc["name_session"] = new_name
        # Pass the document itself to replace_item to prevent forwarding partition_key to aiohttp
        await self.sessions_container.replace_item(
            item=doc,
            body=doc
        )

    #-----------------------------------------------------------------------------------------
    #region             Listado y eliminación de sesiones
    #-----------------------------------------------------------------------------------------

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        """Obtiene todas las sesiones de un usuario específico."""
        query = """
            SELECT c.id, c.name_session, c.fecha_creacion, c.channel
            FROM c
            WHERE c.user_id = @user_id
            ORDER BY c.fecha_creacion DESC
        """
        params = [{"name": "@user_id", "value": user_id}]

        items = []
        async for item in self.sessions_container.query_items(
            query=query,
            parameters=params
        ):
            items.append({
                "session_id": item["id"],
                "session_name": item.get("name_session", "Chat"),
                "created_at": item.get("fecha_creacion"),
                "channel": item.get("channel", "web")
            })

        return items

    async def get_full_session_messages(self, session_id: str) -> List[dict]:
        """Obtiene todos los mensajes de una sesión con información completa."""
        query = """
            SELECT c.id, c.user_query, c.user_question, c.ia_response, c.created_at, c.rate, c.citations
            FROM c
            WHERE c.session_id = @session_id
            ORDER BY c.created_at ASC
        """
        params = [{"name": "@session_id", "value": session_id}]

        messages = []
        async for item in self.messages_container.query_items(
            query=query,
            parameters=params,
            partition_key=session_id
        ):
            # Agregar mensaje del usuario
            messages.append({
                "id": f"{item['id']}-user",
                "role": "user",
                "content": item.get("user_query") or item.get("user_question", ""),
                "created_at": item.get("created_at"),
                "rate": None,
                "files": None
            })
            # Agregar respuesta del asistente
            messages.append({
                "id": item["id"],
                "role": "assistant",
                "content": item.get("ia_response", ""),
                "created_at": item.get("created_at"),
                "rate": item.get("rate"),
                "files": None,
                "citations": item.get("citations", [])
            })

        return messages

    async def get_session_info(self, session_id: str) -> dict:
        """Obtiene la información de una sesión específica."""
        try:
            session = await self.sessions_container.read_item(
                item=session_id,
                partition_key=session_id
            )
            return {
                "session_id": session["id"],
                "session_name": session.get("name_session", "Chat"),
                "user_id": session.get("user_id"),
                "user_email": session.get("user_email")
            }
        except exceptions.CosmosResourceNotFoundError:
            return None

    async def delete_session(self, session_id: str) -> int:
        """
        Elimina una sesión y todos sus mensajes asociados.
        Retorna el número de documentos eliminados.
        """
        deleted_count = 0

        # 1. Eliminar todos los mensajes de la sesión
        query = "SELECT c.id FROM c WHERE c.session_id = @session_id"
        params = [{"name": "@session_id", "value": session_id}]

        message_ids = []
        async for item in self.messages_container.query_items(
            query=query,
            parameters=params,
            partition_key=session_id
        ):
            message_ids.append(item["id"])

        for msg_id in message_ids:
            try:
                await self.messages_container.delete_item(
                    item=msg_id,
                    partition_key=session_id
                )
                deleted_count += 1
            except exceptions.CosmosResourceNotFoundError:
                pass

        # 2. Eliminar la sesión
        try:
            await self.sessions_container.delete_item(
                item=session_id,
                partition_key=session_id
            )
            deleted_count += 1
        except exceptions.CosmosResourceNotFoundError:
            pass

        return deleted_count

#-----------------------------------------------------------------------------------------
#region             Instancia del cliente
#-----------------------------------------------------------------------------------------

# Crea una instancia global del proveedor de servicios de Azure Cosmos DB
cosmos_provider : AzureCosmosDB = AzureCosmosDB()

class CosmosProvider:
    def __init__(self):
        raise NotImplementedError("Cosmos DB integration has been disabled")

    @staticmethod
    def get_instance():
        return None