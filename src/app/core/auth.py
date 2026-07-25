import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.app.core.settings import settings  # Securely imports your clean settings object


class Auth0JWTBearer:
    def __init__(self):
        self.security = HTTPBearer()
        self.jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        self._jwk_client = None

    @property
    def jwk_client(self) -> PyJWKClient:
        """Lazy-init a PyJWKClient, which fetches + caches Auth0's JWKS and
        resolves the correct signing key for a given token's `kid` header."""
        if not self._jwk_client:
            self._jwk_client = PyJWKClient(self.jwks_url)
        return self._jwk_client

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        # BYPASS AUTH0: Return a dummy user payload directly
        return {"sub": "bypassed-user", "gty": "client-credentials"}

        # --- Original validation code (currently bypassed) ---
        # if not settings.AUTH0_DOMAIN or not settings.AUTH0_AUDIENCE:
        #     return {"info": "Auth0 security skipped - variables missing from runtime workspace environment."}
        # 
        # token = credentials.credentials
        # try:
        #     signing_key = self.jwk_client.get_signing_key_from_jwt(token).key
        #     payload = jwt.decode(
        #         token,
        #         signing_key,
        #         algorithms=["RS256"],
        #         audience=settings.AUTH0_AUDIENCE,
        #         issuer=f"https://{settings.AUTH0_DOMAIN}/"
        #     )
        #     return payload
        # 
        # except Exception as e:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail=f"Invalid or expired security token credentials: {str(e)}"
        #     )


# Global authorization dependency initialization hook
auth_required = Auth0JWTBearer()
