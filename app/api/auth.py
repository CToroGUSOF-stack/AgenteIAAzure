## _______________________________________________________________________________________
## En este archivo se definen los endpoints de autenticación de la API utilizando FastAPI.
## 1. `/login`: Inicia el flujo de autenticación OAuth2 con Azure AD.
## 2. `/token`: Intercambia el código de autorización por un token de acceso.
## 3. `/test`: Un endpoint de prueba que devuelve un estado "ok".
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

from fastapi import Request, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse

from app.core.config import settings
from app.core.config import settings
from app.core.middleware import settings_auth, AuthManager, AUTH_DISABLED, DEV_USER



# -----------------------------------------------------------------------------------------
# region             Configuración inicial de servicios
# -----------------------------------------------------------------------------------------

router = APIRouter()



# -----------------------------------------------------------------------------------------
# region             Endpoint GET /login
# -----------------------------------------------------------------------------------------

@router.get("/login")
def login(request: Request):
    """
    Inicia el flujo de autenticación OAuth2 con Microsoft Entra ID (Azure AD).

    Redirige al usuario a la página de login de Microsoft.
    Si la autenticación está deshabilitada (modo desarrollo), redirige inmediatamente
    al frontend con un código falso 'dev_mode'.

    Query params:
        prompt (opcional): Si se incluye, fuerza al usuario a re-autenticarse.
    """
    # =====================================================================
    # MODO DESARROLLO: Bypass de login (Short-circuit)
    # =====================================================================
    if AUTH_DISABLED:
        # Redirige inmediatamente al frontend con un código falso
        # Asume que redirect_uri apunta al frontend (http://localhost)
        dev_redirect = f"{settings_auth.redirect_uri}?code=dev_mode"
        return RedirectResponse(dev_redirect)

    prompt = request.query_params.get('prompt', None)

    if prompt:
        redirect_uri = settings_auth.client_instance.get_authorization_request_url(
            settings_auth.scopes_api,
            redirect_uri=settings_auth.redirect_uri,
            prompt='login'
        )
    else:
        redirect_uri = settings_auth.client_instance.get_authorization_request_url(
            settings_auth.scopes_api,
            redirect_uri=settings_auth.redirect_uri
        )

    return RedirectResponse(redirect_uri)



# -----------------------------------------------------------------------------------------
# region             Endpoint GET /token
# -----------------------------------------------------------------------------------------

@router.get("/token")
async def auth_token(request: Request):
    """
    Callback endpoint que recibe el código de autorización de Azure AD
    y lo intercambia por un token de acceso.

    Query params:
        code: El código de autorización retornado por Azure AD.

    Returns:
        JSON con access_token, nombre del usuario y permisos/roles.
        En modo desarrollo, si el código es 'dev_mode', retorna un token ficticio.
    """
    code = request.query_params.get("code")

    # =====================================================================
    # MODO DESARROLLO: Intercambio de código falso
    # =====================================================================
    if AUTH_DISABLED and code == "dev_mode":
        return JSONResponse(content={
            "access_token": "dev_token_bypass",
            "user_id": DEV_USER.id,
            "name": DEV_USER.name,
            "permissions": DEV_USER.roles
        }, status_code=200)

    if not code:
        return JSONResponse(
            content={"error": "No se recibió código de autorización"},
            status_code=400
        )

    try:
        # Intercambia el código por tokens
        result = settings_auth.client_instance.acquire_token_by_authorization_code(
            code=code,
            scopes=settings_auth.scopes_api,
            redirect_uri=settings_auth.redirect_uri
        )

        if "error" in result:
            return JSONResponse(
                content={"error": result.get("error_description", "Error desconocido")},
                status_code=400
            )

        # Extrae información del usuario desde el token
        access_token = result.get("access_token")
        id_token = result.get("id_token")  # ID token tiene audience = client_id
        id_token_claims = result.get("id_token_claims", {})

        # Stable user ID from claims (oid is preferred for Entra ID, sub is fallback)
        stable_user_id = id_token_claims.get("oid", id_token_claims.get("sub"))

        # NOTA: Cuando usamos User.Read, el access_token es para Microsoft Graph,
        # pero el id_token es para nuestra aplicación. Usamos id_token para autenticación.
        # Si tienes scopes personalizados de API, el access_token tendrá el audience correcto.
        token_to_return = id_token if id_token else access_token

        user_info = {
            "access_token": token_to_return,
            "user_id": stable_user_id,
            "name": id_token_claims.get("name", "Unknown"),
            "permissions": id_token_claims.get("roles", [])
        }

        return JSONResponse(content=user_info, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

