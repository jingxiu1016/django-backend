"""******************************** 开始
    author:惊修
    time:$
   ******************************* 结束"""

from rest_framework.authentication import BaseAuthentication
import jwt
from jwt import exceptions
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

class jwtQueryParamsBaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers['Authorization']
        salt = settings.SECRET_KEY
        try:
            payload = jwt.decode(token,salt,True)
        except exceptions.ExpiredSignatureError:
            raise AuthenticationFailed({'status':1003,'error':'token已失效'})
        except jwt.DecodeError:
            raise AuthenticationFailed({'status': 1003, 'error': 'token认证失败'})
        except jwt.InvalidTokenError:
            raise AuthenticationFailed({'status': 1003, 'error': '非法的token'})

        return (payload,token)