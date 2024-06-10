from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout

from bank.models import BankAccount

# Create your views here.
@login_required(login_url='login')
def index(request):
    list_user_bank = BankAccount.objects.filter(user=request.user).order_by('balance')[:4]
    for user_bank in list_user_bank:
        pass
    return render(request=request, template_name='index.html',context={'list_user_bank':list_user_bank})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')  # Replace 'home' with your home page URL name
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request=request, template_name='login.html')

def user_logout(request):
    logout(request)
    return redirect('index')