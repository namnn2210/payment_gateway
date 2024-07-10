from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bank.models import BankAccount
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
    Notification.objects.create(recipient=request.user, message='Welcome to our website!')
    list_user_bank = BankAccount.objects.filter(user=request.user, status=True)
    notifications = request.user.notifications.filter(read=False).order_by('-created_at')
    # print(list(notifications)
    return render(request=request, template_name='index.html',context={'list_user_bank':list_user_bank,'notifications':list(notifications)})

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

@csrf_exempt
def send_notification(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'send_notification',
            'message': 'Hello, this is a real-time notification!'
        }
    )
    return JsonResponse({'status': 200, 'message': 'Done', 'data': 'ok'})

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            # Verify the payload signature
            secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '226pay')
            signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            if not signature:
                return JsonResponse({'status': 'error', 'message': 'Missing signature'}, status=400)

            sha_name, signature = signature.split('=')
            if sha_name != 'sha1':
                return JsonResponse({'status': 'error', 'message': 'Unsupported signature format'}, status=400)

            mac = hmac.new(secret.encode(), msg=request.body, digestmod=hashlib.sha1)
            if not hmac.compare_digest(mac.hexdigest(), signature):
                return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

            # Load JSON payload
            payload = json.loads(request.body.decode('utf-8'))

            # Check the branch (refs/heads/main for the main branch)
            if payload.get('ref') == 'refs/heads/main':  # Change 'main' to your branch if needed
                # Get the current working directory
                cwd = os.getcwd()
                # Run the deployment script
                subprocess.call(['git', '-C', cwd, 'pull'])

                return JsonResponse({'status': 'success', 'message': 'Deployment script executed.'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': 'Branch not matched'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def user_logout(request):
    logout(request)
    return redirect('index')


def user_callback(request):
    return JsonResponse({'status': 200, 'message': 'Done', 'data': 'ok'})