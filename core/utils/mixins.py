from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

from apikey.models import ApiKeyModel

class APIKeyMissingException(APIException):
    status_code = 400
    default_detail = 'apikey ارسال نشده است'
    default_code = 'api_key_missing'

class APIKeyInvalidException(APIException):
    status_code = 400
    default_detail = 'API key نامعتبر است'
    default_code = 'api_key_invalid'

class ApiKeyValidationMixin:
    def check_api_key(self, request):
        key = request.headers.get('apikey')
        if not key:
            raise APIKeyMissingException()
        
        apikey = ApiKeyModel.objects.filter(key=key).first()
        if not apikey:
            raise APIKeyInvalidException()
        
        # Attach useful information to the request
        request.business_id = apikey.business.id
        request.get_message = apikey.get_message