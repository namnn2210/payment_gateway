from django.shortcuts import render, redirect, get_object_or_404
from .models import EmployeeDeposit
from bank.models import BankAccount
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .serializers import DepositSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status
from cms.models import APIResponse
import json

# Create your views here.
@csrf_exempt
@permission_classes([IsAuthenticated])
def employee_deposit(request):
    jwt_auth = JWTAuthentication()
    try:
        user_auth_tuple = jwt_auth.authenticate(request)
        if user_auth_tuple is None:
            raise AuthenticationFailed('No user found from token or invalid token.')
        user = user_auth_tuple[0]  # The user is the first element in the tuple
    except AuthenticationFailed as e:
        return JsonResponse({'status': 403, 'message': str(e)}, status=403)

    if request.method == 'POST':
        deposit_amount = int(request.POST.get('deposit', 0))
        bank_id = int(request.POST.get('bank'))
        bank = BankAccount.objects.filter(id=bank_id).first()
        EmployeeDeposit.objects.create(
            user = request.user,
            amount = deposit_amount,
            bankname = bank.bank_name,
            accountno = bank.account_number,
            accountname = bank.account_name,
            bankcode = bank.bank_name.bankcode
        )
        return Response(APIResponse(success=True, message="").__dict__(), status=status.HTTP_201_CREATED)
    if user.is_superuser:
        list_deposit_requests = EmployeeDeposit.objects.filter(status=False)
    else:
        list_deposit_requests = EmployeeDeposit.objects.filter(user=request.user)
    list_deposit_requests = list_deposit_requests.order_by('-created_at')
        
    deposit_serializer = DepositSerializer(list_deposit_requests, many=True).data

    return JsonResponse({'success': True, 'data': {'list_deposit': deposit_serializer}, 'message': ""}, status=200)



@csrf_exempt
@require_POST
def update_deposit(request):
    try:
        data = json.loads(request.body)
        deposit_id = data.get('id')
        deposit = EmployeeDeposit.objects.filter(id=deposit_id).first()
        deposit.status = True
        deposit.save()
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
    
@csrf_exempt
@require_POST
def delete_deposit(request):
    try:
        data = json.loads(request.body)
        deposit_id = data.get('id')
        deposit = EmployeeDeposit.objects.filter(id=deposit_id).first()
        
        deposit.delete()
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})