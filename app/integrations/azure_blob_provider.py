## _______________________________________________________________________________________
## En este archivo se define un proveedor asíncrono para Azure Blob Storage.
## Proporciona métodos para subir, descargar, generar SAS y eliminar blobs.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import os
import logging
from datetime import datetime, timedelta
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from app.core.config import settings



# -----------------------------------------------------------------------------------------
# region             Clase AzureBlobStorage
# -----------------------------------------------------------------------------------------

class AzureBlobStorage:
    """
    Proveedor asíncrono para Azure Blob Storage.
    Gestiona la conexión y las operaciones de blob (upload, download, delete, SAS).
    """

    def __init__(self):
        self.account_name = settings.storage.azure_storage_account_name
        self.container_name = settings.storage.azure_storage_container_userfiles
        self._client = None

    def get_client(self) -> BlobServiceClient:
        """
        Retorna un cliente asíncrono de BlobServiceClient.
        Usa la clave de almacenamiento si está disponible, de lo contrario usa DefaultAzureCredential.
        """
        if self._client:
            return self._client

        account_url = f"https://{self.account_name}.blob.core.windows.net"
        account_key = os.getenv("AZURE_STORAGE_KEY")

        if account_key:
            # Authenticate using Account Key
            self._client = BlobServiceClient(account_url, credential=account_key)
        else:
            # Fallback to Managed Identity / AZ CLI
            from azure.identity import DefaultAzureCredential
            self._client = BlobServiceClient(account_url, credential=DefaultAzureCredential())

        return self._client

    def generate_upload_sas(self, blob_name: str, duration_minutes: int = 15) -> str:
        """
        Genera una URL SAS para subir un blob (operación síncrona).

        Args:
            blob_name: Nombre del blob.
            duration_minutes: Duración de la SAS en minutos.

        Returns:
            URL SAS completa.
        """
        account_key = os.getenv("AZURE_STORAGE_KEY")

        # Nota: generate_blob_sas requiere la clave de cuenta.
        # Si no hay clave, se necesitaría una clave de delegación de usuario (más complejo).
        if not account_key:
            logging.warning("AZURE_STORAGE_KEY not found. SAS generation might fail unless running with delegation.")
            # Fallback logic here if needed

        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(create=True, write=True),
            expiry=datetime.utcnow() + timedelta(minutes=duration_minutes)
        )

        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    async def download_blob(self, blob_name: str) -> bytes:
        """
        Descarga el contenido de un blob como bytes usando el cliente asíncrono.

        Args:
            blob_name: Nombre del blob.

        Returns:
            Contenido del blob en bytes.
        """
        client = self.get_client()
        blob_client = client.get_blob_client(container=self.container_name, blob=blob_name)
        stream = await blob_client.download_blob()
        data = await stream.readall()
        return data

    def get_blob_url(self, blob_name: str) -> str:
        """Retorna la URL pública (o con SAS) del blob."""
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

    async def upload_blob(self, blob_name: str, data: bytes, content_type: str = None):
        """
        Sube bytes a un blob (asíncrono). Sobrescribe si existe.

        Args:
            blob_name: Nombre del blob.
            data: Contenido en bytes.
            content_type: Tipo MIME del contenido (opcional).
        """
        try:
            client = self.get_client()
            blob_client = client.get_blob_client(container=self.container_name, blob=blob_name)

            # content_settings permite establecer el Content-Type en el blob
            from azure.storage.blob import ContentSettings
            my_content_settings = ContentSettings(content_type=content_type) if content_type else None

            await blob_client.upload_blob(data, overwrite=True, content_settings=my_content_settings)
            logging.info(f"Uploaded blob: {blob_name}")
            return self.get_blob_url(blob_name)

        except Exception as e:
            logging.error(f"Error uploading blob {blob_name}: {e}")
            raise

    async def delete_blobs_prefix(self, prefix: str):
        """
        Elimina todos los blobs que comiencen con un prefijo.
        Maneja ADLS Gen2 (espacio de nombres jerárquico) eliminando primero los archivos hoja.

        Args:
            prefix: Prefijo de los blobs a eliminar.
        """
        logging.info(f"Attempting to delete blobs with prefix: '{prefix}' in container '{self.container_name}'")
        try:
            client = self.get_client()
            container_client = client.get_container_client(self.container_name)

            # Collect all blobs first to handle the deletion order
            # In ADLS Gen2, we must delete leaf nodes (files) before parents (directories)
            blobs_to_delete = []
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs_to_delete.append(blob.name)

            if not blobs_to_delete:
                logging.warning(f"No blobs found with prefix: '{prefix}'")
                return

            # Sort by length descending (longest paths first = leaf nodes)
            blobs_to_delete.sort(key=len, reverse=True)

            count = 0
            for blob_name in blobs_to_delete:
                try:
                    await container_client.delete_blob(blob_name)
                    logging.info(f"Successfully deleted: {blob_name}")
                    count += 1
                except Exception as e:
                    # If it's a directory that still has something, we log it and continue
                    logging.warning(f"Could not delete {blob_name}: {str(e)}")

            # [HNS Support] Explicitly try to delete the directory blob itself
            # In HNS accounts, the directory exists as a resource.
            directory_blob = prefix.rstrip("/")
            if directory_blob:
                try:
                    await container_client.delete_blob(directory_blob)
                    logging.info(f"Successfully deleted directory blob: {directory_blob}")
                except ResourceNotFoundError:
                    # Expected if it's a standard blob account (virtual directory) or already gone
                    pass
                except Exception as e:
                    logging.warning(f"Could not delete directory blob {directory_blob}: {e}")

            logging.info(f"Total items deleted: {count}")

        except Exception as e:
            logging.error(f"Error during delete_blobs_prefix for '{prefix}': {str(e)}")
            raise



# -----------------------------------------------------------------------------------------
# region             Instancia global
# -----------------------------------------------------------------------------------------

blob_provider = AzureBlobStorage()

