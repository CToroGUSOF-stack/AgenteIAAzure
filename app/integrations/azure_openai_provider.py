## _______________________________________________________________________________________
## En este archivo se define un proveedor para los servicios de Azure OpenAI.
## Se encarga de inicializar los modelos de chat y de embeddings utilizando las
## credenciales y configuraciones definidas en la aplicación.
## _______________________________________________________________________________________

#-----------------------------------------------------------------------------------------
#region             Librerías
#-----------------------------------------------------------------------------------------

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from app.core.config import settings

#-----------------------------------------------------------------------------------------
#region             Clase para el cliente de Azure OpenAI
#-----------------------------------------------------------------------------------------

class AzureOpenAI:
    """
    Clase que encapsula la lógica para inicializar y gestionar
    los modelos de Azure OpenAI.
    """
    def __init__(self):
        # Obtiene las credenciales desde la configuración de la aplicación
        api_key: str = settings.ai_services.azure_openai_api_key
        api_version: str = settings.ai_services.openai_api_version
        azure_endpoint: str = settings.ai_services.azure_openai_endpoint

        # Valida que las variables de entorno no sean nulas
        if not api_key:
            raise ValueError("Azure OpenAI API Key no puede ser None")
        if not api_version:
            raise ValueError("Azure OpenAI API Version no puede ser None")
        if not azure_endpoint:
            raise ValueError("Azure OpenAI Endpoint no puede ser None")
        
        # Inicializa el modelo de chat con los parámetros de configuración
        self.model_ai: AzureChatOpenAI = AzureChatOpenAI(
            azure_deployment = settings.ai_services.model_ia_name,
            api_version=api_version,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            temperature=1
        )
        
        # Inicializa el modelo de embeddings con los parámetros de configuración
        self.model_embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
            api_key = api_key, 
            api_version = api_version,
            azure_endpoint = azure_endpoint,
            azure_deployment = settings.ai_services.model_embeddings_name
        )

#-----------------------------------------------------------------------------------------
#region             Instancia del cliente
#-----------------------------------------------------------------------------------------

# Crea una instancia global del proveedor de servicios de Azure OpenAI
openai_provider : AzureOpenAI = AzureOpenAI()