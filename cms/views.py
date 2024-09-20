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
from employee.models import EmployeeWorkingSession
from cms.models import User2Fa
from io import BytesIO
import pyotp
import qrcode
import base64
from PIL import Image
from django.utils import timezone
from datetime import datetime

TWO_FA_EXPIRATION_TIME = 21600 

# Create your views here.
@login_required(login_url='user_login')
def index(request):
    user_2fa = User2Fa.objects.filter(user=request.user).first()
    # if user_2fa.is_2fa_enabled:
    #     return render(request, '2fa.html')
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

    session = EmployeeWorkingSession.objects.filter(status=False, user=request.user).first()
    if session:
        is_session = True
    else:
        is_session = False
    
        
    return render(request=request, template_name='index.html', context={'list_user_bank':list_user_bank,'list_deposit_requests':list_deposit_requests,'list_bank_option':list_bank_option, 'is_session':is_session})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            user_2fa = User2Fa.objects.filter(user=user).first()
            if user_2fa and user_2fa.is_2fa_enabled:
                return redirect('verify_otp')
            return redirect('setup_2fa')
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

@login_required(login_url='user_login')
def setup_2fa(request):
    user_2fa, created = User2Fa.objects.get_or_create(user=request.user)
    if not user_2fa.otp_secret:
        user_2fa.otp_secret = pyotp.random_base32()
        user_2fa.save()

    totp = pyotp.TOTP(user_2fa.otp_secret)
    totp_uri = totp.provisioning_uri(name=request.user.username, issuer_name="226Pay")

    qr = qrcode.make(totp_uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        print(otp_code)
        if totp.verify(otp_code):
            user_2fa.is_2fa_enabled = True
            user_2fa.last_verified = timezone.now()
            user_2fa.save()
            request.session['is_2fa_verified'] = True
            request.session['2fa_verified_at'] = timezone.now().timestamp()
            return redirect('index')
        else:
            return render(request, 'setup_2fa.html', {"error": "Invalid OTP", "qr_code": qr_code_base64, "totp_secret": user_2fa.otp_secret})
    return render(request, 'setup_2fa.html', {"qr_code": qr_code_base64, "totp_secret": user_2fa.otp_secret})

@login_required(login_url='user_login')
def verify_otp(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        user_2fa = User2Fa.objects.filter(user=request.user).first()
        if user_2fa:
            totp = pyotp.TOTP(user_2fa.otp_secret)
            if totp.verify(otp_code):
                request.session['is_2fa_verified'] = True
                request.session['2fa_verified_at'] = timezone.now().timestamp()
                user_2fa.last_verified = timezone.now()
                user_2fa.save()
                return redirect('index')
            else:
                return render(request, 'verify_otp.html', {"error": "Invalid OTP"})
    return render(request, 'verify_otp.html')
        
@login_required(login_url='user_login')
def submit_otp(request):
    if request.method == "POST":
        otp_code = request.POST.get("otpCode")
        user_2fa = User2Fa.objects.filter(user=request.user).first()
        totp = pyotp.TOTP(user_2fa.otp_secret)

        if totp.verify(otp_code):
            user_2fa.is_2fa_enabled = True
            user_2fa.save()
            return redirect('index')
        else:
            return render(request, '2fa.html', {"error": "Invalid OTP"})

def user_logout(request):
    logout(request)
    return redirect('index')