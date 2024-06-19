from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse

from bank.models import BankAccount
from notification.models import Notification

# Create your views here.
@login_required(login_url='login')
def index(request):
    Notification.objects.create(recipient=request.user, message='Welcome to our website!')
    list_user_bank = BankAccount.objects.filter(user=request.user, status=True)
    notifications = request.user.notifications.filter(read=False).order_by('-created_at')
    # print(list(notifications)
    return render(request=request, template_name='index.html',context={'list_user_bank':list_user_bank,'notifications':list(notifications)})

def login(request):
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


def user_callback(request):
    print("eheheheheh")
    print(request)
    return JsonResponse({'status': 200, 'message': 'Done', 'data': 'ok'})