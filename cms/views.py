
from cms.models import APIResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.http import JsonResponse
from django.contrib.auth import login as django_login
from .serializers import UserSerializer
from django.contrib.auth.models import User
import json

 # Disable CSRF for this view
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    if request.method == 'POST':
        print(request.method)
        print(request.body)
        body = json.loads(request.body.decode('utf-8'))
        username = body['username']
        password = body['password']

        if not username or not password:
            return Response(APIResponse(success=False, data={}, message="Tên đăng nhập và mật khẩu là bắt buộc").__dict__(),
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(APIResponse(success=False, data={}, message="Thông tin đăng nhập không chính xác").__dict__(),
                            status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response(APIResponse(success=False, data={}, message="Thông tin đăng nhập không chính xác").__dict__(),
                            status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response(APIResponse(success=False, data={},
                                        message="Tài khoản bị khóa. Vui lòng liên hệ để biết thêm chi tiết").__dict__(),
                            status=status.HTTP_401_UNAUTHORIZED)

        django_login(request, user)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        user_serializer = UserSerializer(user).data

        print(access_token, user_serializer)

        return Response(APIResponse(success=True, data={'token': access_token, 'user': user_serializer},
                                    message="").__dict__(), status=status.HTTP_200_OK)
    


def jwt_auth_check(request):
    jwt_auth = JWTAuthentication()
    try:
        user_auth_tuple = jwt_auth.authenticate(request)
        if user_auth_tuple is None:
            raise AuthenticationFailed('No user found from token or invalid token.')
        user = user_auth_tuple[0]  # The user is the first element in the tuple
        return user
    except AuthenticationFailed as e:
        return JsonResponse({'status': 403, 'message': str(e)}, status=403)