from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer
from src.auth.exceptions import UnauthorizedException, UnauthenticatedException
from fastapi import Depends
from typing import Optional
from src.config import get_settings
import jwt


class VerifyToken:
    """Does all the token verification using PyJWT"""

    def __init__(self):
        self.config = get_settings()

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f'https://{self.config.auth0_domain}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

        # 👇 new code
    async def verify(self,
                     security_scopes: SecurityScopes,
                     token: Optional[HTTPAuthorizationCredentials] = Depends(
                         HTTPBearer())
                     ):
        if token is None:
            raise UnauthenticatedException

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:

            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.config.auth0_algorithms,
                audience=self.config.auth0_api_audience,
                issuer=self.config.auth0_issuer,
            )

        except Exception as error:
            print(
                f"incoming issuer internal: {self.config.auth0_issuer}")

            raise UnauthorizedException(str(error))

        return payload
