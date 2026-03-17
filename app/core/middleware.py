## _______________________________________________________________________________________
## En este archivo se define el middleware de autenticación para la API.
## Se utiliza MSAL para validar tokens JWT emitidos por Azure AD (Entra ID).
##
## MODO DESARROLLO: Set AUTH_DISABLED=true en .env para desactivar autenticación
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import os
import jwt
from jwt import PyJWKClient
import logging
from typing import Optional, List
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings


# -----------------------------------------------------------------------------------------
# region             Configuración de modo desarrollo
# -----------------------------------------------------------------------------------------

# Si AUTH_DISABLED=true, se omite la validación de tokens (solo para desarrollo)
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "false").lower() == "true"

if AUTH_DISABLED:
    logging.warning("AUTHENTICATION DISABLED - Development mode only!")


# -----------------------------------------------------------------------------------------
# region             Modelos
# -----------------------------------------------------------------------------------------

class User(BaseModel):
    """Modelo que representa al usuario autenticado."""
    id: str
    name: str
    email: Optional[str] = None
    roles: List[str] = []


# -----------------------------------------------------------------------------------------
# region             Usuario de desarrollo (mock)
# -----------------------------------------------------------------------------------------

DEV_USER = User(
    id="dev-user-001",
    name="Developer",
    email="developer@localhost",
    roles=["admin", "user"]
)


# -----------------------------------------------------------------------------------------
# region             Configuración de autenticación
# -----------------------------------------------------------------------------------------

class AuthSettings:
    """Configuración para la autenticación con Azure AD."""

    def __init__(self):
        self.client_id = settings.auth.client_id
        self.client_secret = settings.auth.client_secret
        self.tenant_id = settings.auth.tenant_id
        self.authority = settings.auth.authority
        self.jwks_url = settings.auth.jwks_url
        self.redirect_uri = settings.auth.redirect_uri
        self.scopes_api = settings.auth.scopes

        # Solo inicializar MSAL si la autenticación está habilitada
        self.client_instance = None
        if not AUTH_DISABLED and self.client_id and self.client_secret:
            try:
                from msal import ConfidentialClientApplication
                self.client_instance = ConfidentialClientApplication(
                    client_id=self.client_id,
                    client_credential=self.client_secret,
                    authority=self.authority
                )
            except Exception as e:
                logging.warning(f"MSAL not initialized: {e}")

# Instancia global de configuración de autenticación
settings_auth = AuthSettings()


# -----------------------------------------------------------------------------------------
# region             Bearer Token Security
# -----------------------------------------------------------------------------------------

security = HTTPBearer(auto_error=False)


# -----------------------------------------------------------------------------------------
# region             AuthManager - Dependencia para validar tokens
# -----------------------------------------------------------------------------------------

class AuthManager:
    """
    Clase para gestionar la autenticación y validación de tokens JWT.
    Se usa como dependencia en los endpoints protegidos.

    En modo desarrollo (AUTH_DISABLED=true), retorna un usuario mock.
    """

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decodifica y valida un token JWT.
        En producción, valida la firma con las claves públicas de Azure AD (JWKS).
        """
        try:
            # =================================================================
            # Modo Desarrollo: Decodificación simple sin validar firma
            # =================================================================
            if AUTH_DISABLED:
                return jwt.decode(
                    token,
                    options={"verify_signature": False},
                    algorithms=["RS256"]
                )

            # =================================================================
            # Modo Producción: Validación completa con JWKS
            # =================================================================

            # 1. Obtener la clave pública de firma desde Azure AD
            jwks_client = PyJWKClient(settings_auth.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # 2. Decodificar y validar firma, audiencia e issuer
            # Necesitamos definir el issuer esperado
            # Azure AD v2 issuer format: https://login.microsoftonline.com/{tenant_id}/v2.0
            expected_issuer = f"https://login.microsoftonline.com/{settings_auth.tenant_id}/v2.0"

            # La audiencia suele ser el Client ID (si usamos accessTokenAcceptedVersion: 2)
            # o api://{client_id} dependiendo de la configuración.
            # Como fallback aceptamos ambos o el configurado.
            expected_audience = settings_auth.client_id

            payload = jwt.decode(
                token,
                key=signing_key.key,
                algorithms=["RS256"],
                audience=expected_audience,
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True
                }
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="El token ha expirado")
        except jwt.InvalidTokenError as e:
            logging.error(f"Token inválido: {str(e)}")
            raise HTTPException(status_code=401, detail="Token inválido o malformado")
        except Exception as e:
            logging.error(f"Error inesperado validando token: {str(e)}")
            raise HTTPException(status_code=401, detail="Falló la autenticación del token")

    @staticmethod
    def decode_user(token: str) -> User:
        """Extrae la información del usuario desde el token."""
        decoded = AuthManager.decode_token(token)

        return User(
            # "oid" (Object ID) es el identificador único e inmutable del usuario en el directorio
            id=decoded.get("oid", decoded.get("sub", "")),
            name=decoded.get("name", "Usuario"),
            # "preferred_username" suele ser el email/UPN
            email=decoded.get("preferred_username", decoded.get("email")),
            roles=decoded.get("roles", [])
        )

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """
        Valida el token de autorización y retorna el usuario.
        Se usa como dependencia: user: User = Depends(auth_manager)

        En modo desarrollo (AUTH_DISABLED=true), retorna un usuario mock sin validar.
        """
        # =====================================================================
        # MODO DESARROLLO: Omitir autenticación
        # =====================================================================
        if AUTH_DISABLED:
            request.state.user = DEV_USER
            return DEV_USER

        # =====================================================================
        # MODO PRODUCCIÓN: Validar token
        # =====================================================================
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="No se proporcionó token de autorización"
            )

        token = credentials.credentials
        user = self.decode_user(token)

        # Almacena el usuario en el estado de la request para uso posterior
        request.state.user = user

        return user


# -----------------------------------------------------------------------------------------
# region             Instancia global del AuthManager
# -----------------------------------------------------------------------------------------

auth_manager = AuthManager()

