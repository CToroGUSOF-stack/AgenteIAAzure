## _______________________________________________________________________________________
## En este archivo se gestiona la configuración de la aplicación.
## Se cargan las variables de entorno y se organizan en clases por servicio.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())


# -----------------------------------------------------------------------------------------
# region                         Settings principal
# -----------------------------------------------------------------------------------------

class Settings:
    """
    Clase principal de configuración que agrupa todas las subconfiguraciones
    por servicio (general, autenticación, IA, Cosmos, almacenamiento).
    """

    class GeneralSettings:
        """Configuraciones generales de la aplicación."""

        def __init__(self):
            # General application settings
            self.cosmos_db_enabled: bool = os.getenv("COSMOS_DB_ENABLED", "true").lower() == "true"
            # Puedes agregar otras configuraciones generales aquí
            self.environment: str = os.getenv("ENVIRONMENT", "production")

    class AuthServices:
        """Configuraciones de autenticación con Azure AD / Entra ID."""

        def __init__(self):
            # Azure AD / Entra ID settings
            # Client ID de la aplicación registrada en Azure AD
            self.client_id: str = os.getenv("AZURE_AD_CLIENT_ID", "")
            # Client Secret de la aplicación
            self.client_secret: str = os.getenv("AZURE_AD_CLIENT_SECRET", "")
            # Tenant ID de Azure AD
            self.tenant_id: str = os.getenv("AZURE_AD_TENANT_ID", "")
            # Authority URL para autenticación
            self.authority: str = f"https://login.microsoftonline.com/{self.tenant_id}"
            # OpenID Connect Discovery URL
            self.discovery_url: str = f"{self.authority}/v2.0/.well-known/openid-configuration"
            # JWKS URL (Generated, though middleware might fetch from discovery)
            self.jwks_url: str = f"{self.authority}/discovery/v2.0/keys"

            # Redirect URI después de login
            self.redirect_uri: str = os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:8000/api/auth/token")
            # Scopes para la API
            # NOTA: 'openid', 'profile', y 'offline_access' son reservados y MSAL los agrega automáticamente.
            # Si no tienes scopes personalizados, usa 'User.Read' de Microsoft Graph.
            raw_scope = os.getenv("AZURE_AD_SCOPE", "User.Read")
            reserved = {"openid", "profile", "offline_access", ""}
            if raw_scope.lower() in reserved:
                self.scopes: list = ["User.Read"]  # Default para sign-in
            else:
                self.scopes: list = [raw_scope]

    class AIServices:
        """Configuraciones de servicios de IA (Azure OpenAI, Search, Document Intelligence)."""

        def __init__(self):
            # Azure AI Services settings
            # Clave de API para Azure OpenAI
            self.azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
            # Versión de la API de OpenAI
            self.openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION")
            # Endpoint de Azure OpenAI
            self.azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
            # Nombre del modelo de IA para el chat
            self.model_ia_name: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
            # Nombre del modelo de embeddings
            self.model_embeddings_name: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            # Endpoint para Azure AI Search
            self.azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT")
            # Clave de API para Azure AI Search
            self.azure_search_key: str = os.getenv("AZURE_SEARCH_KEY")
            # Índice de búsqueda en Azure AI Search
            self.azure_search_index: str = os.getenv("AZURE_SEARCH_INDEX")
            # Índice de búsqueda para documentos de usuario
            self.azure_search_userdocs_index: str = os.getenv("AZURE_SEARCH_USERDOCS_INDEX")
            # Límite de mensajes en la memoria (contexto) del chat
            self.message_memory_limit: int = int(os.getenv("MESSAGE_MEMORY_LIMIT", 5))

            # Document Intelligence
            self.document_intelligence_endpoint: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            self.document_intelligence_key: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    class CosmosServices:
        """Configuraciones de Azure Cosmos DB (actualmente comentada)."""

        def __init__(self):
            # Azure Cosmos DB settings
            # Clave de Azure Cosmos DB
            self.azure_cosmos_key: str = os.getenv("AZURE_COSMOS_DB_KEY")
            # Endpoint de Azure Cosmos DB
            self.azure_cosmos_endpoint: str = os.getenv("AZURE_COSMOS_DB_ENDPOINT")
            # Nombre de la base de datos de Cosmos DB
            self.azure_cosmos_database_name: str = os.getenv("AZURE_COSMOS_DATABASE_NAME")
            # Nombre del contenedor para las sesiones
            self.azure_cosmos_session_container_name: str = os.getenv("AZURE_COSMOS_SESSION_CONTAINER_NAME")
            # Nombre del contenedor para los mensajes
            self.azure_cosmos_message_container_name: str = os.getenv("AZURE_COSMOS_MESSAGE_CONTAINER_NAME")

    class StorageServices:
        """Configuraciones de almacenamiento (Azure Blob Storage y límites de subida)."""

        def __init__(self):
            # Azure Storage and User Upload settings
            self.azure_storage_account_name: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            self.azure_storage_container_userfiles: str = os.getenv("AZURE_STORAGE_CONTAINER_USERFILES", "user-files")
            self.user_upload_max_bytes: int = int(os.getenv("USER_UPLOAD_MAX_BYTES", 16 * 1024 * 1024)) # 16MB default

    def __init__(self):
        self.app_name = "FNG Chatbot"
        self.admin_email = "admin@example.com"

        self.general = self.GeneralSettings()

        self.auth = Settings.AuthServices()
        self.ai_services = Settings.AIServices()
        #self.cosmos_db = Settings.CosmosServices()
        self.storage = Settings.StorageServices()


# -----------------------------------------------------------------------------------------
# region             Instancia global
# -----------------------------------------------------------------------------------------

# Global settings instance
settings = Settings()
