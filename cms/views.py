from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bank.models import BankAccount, Bank
from employee.models import EmployeeDeposit
from django.core.paginator import Paginator
from notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


import subprocess
import hmac
import hashlib
import json
import os

# Create your views here.
@login_required(login_url='user_login')
def index(request):
    list_bank_option = Bank.objects.filter(status=True)
    if request.user.is_superuser:
        list_user_bank = BankAccount.objects.all()
    else:
        list_user_bank = BankAccount.objects.filter(user=request.user)
    if request.user.is_superuser:
        list_deposit_requests = EmployeeDeposit.objects.filter(status=False)
        paginator = Paginator(list_deposit_requests, 10)  # Show 10 items per page
        page_number = request.GET.get('page')
        list_deposit_requests = paginator.get_page(page_number)
    else:
        list_deposit_requests = None
    
        
    return render(request=request, template_name='index.html', context={'list_user_bank':list_user_bank,'list_deposit_requests':list_deposit_requests})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index') 
        else:
            return render(request=request, template_name='login.html', context={'error': 'Invalid username or password. Contact admin for support'})
    return render(request=request, template_name='login.html')

def profile(request):
    if request.method == 'POST':
        current_password = request.POST.get('password')
        new_password = request.POST.get('newpassword')
        new_password2 = request.POST.get('renewpassword')
        if not current_password or not new_password or not new_password2:
            return render(request=request, template_name='profile.html', context={'error': 'Please fill all fields'})
        if new_password != new_password2:
            return render(request=request, template_name='profile.html', context={'error': 'Passwords do not match'})
        if not request.user.check_password(current_password):
            return render(request=request, template_name='profile.html', context={'error': 'Current password is incorrect'})
        request.user.set_password(new_password)
        request.user.save()
        return render(request=request, template_name='profile.html', context={'success': 'Password changed successfully'})
    return render(request=request, template_name='profile.html', context={'error': None})

def user_logout(request):
    logout(request)
    return redirect('index')