## _______________________________________________________________________________________
## En este archivo se define un cliente para interactuar con el servicio de
## Azure AI Search. Se encarga de inicializar el cliente de búsqueda utilizando
## las credenciales y el nombre del índice definidos en la configuración de la aplicación.
## _______________________________________________________________________________________

#-----------------------------------------------------------------------------------------
#region             Librerías
#-----------------------------------------------------------------------------------------

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings

#-----------------------------------------------------------------------------------------
#region             Clase para el cliente de Azure AI Search
#-----------------------------------------------------------------------------------------

class AzureAISearch:
    """
    Clase que encapsula la lógica para inicializar y gestionar
    el cliente de búsqueda de Azure AI Search.
    """
    def __init__(self):
        # Obtiene las credenciales y el nombre del índice desde la configuración
        api_key: str = settings.ai_services.azure_search_key
        service_endpoint: str = settings.ai_services.azure_search_endpoint
        index_name: str = settings.ai_services.azure_search_index

        # Valida que las variables de entorno no sean nulas
        if not api_key:
            raise ValueError("Azure Search API Key no puede ser None")
        if not service_endpoint:
            raise ValueError("Azure Search Service Endpoint no puede ser None")
        if not index_name:
            raise ValueError("Azure Search Index Name no puede ser None")
        
        # Inicializa el cliente de búsqueda con las credenciales obtenidas
        self.client : SearchClient = SearchClient(
            endpoint=service_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )

#-----------------------------------------------------------------------------------------
#region             Instancia del cliente
#-----------------------------------------------------------------------------------------

# Crea una instancia global del proveedor de búsqueda de Azure
ai_search_provider : AzureAISearch = AzureAISearch()