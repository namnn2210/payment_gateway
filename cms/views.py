from django.shortcuts import redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.paginator import Paginator
from .models import User2Fa
from .forms import OTPForm
from bank.models import Bank, BankAccount
from employee.models import EmployeeDeposit, EmployeeWorkingSession
import pyotp
import qrcode
import base64
from io import BytesIO

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'
    login_url = 'cms:user_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        list_bank_option = Bank.objects.filter(status=True)
        list_user_bank = BankAccount.objects.filter(user=user) if not user.is_superuser else BankAccount.objects.all()
        user_online = EmployeeWorkingSession.objects.filter(status=False)

        list_deposit_requests = None
        if user.is_superuser:
            deposits = EmployeeDeposit.objects.filter(status=False)
            paginator = Paginator(deposits, 10)
            page_number = self.request.GET.get('page')
            list_deposit_requests = paginator.get_page(page_number)

        session = EmployeeWorkingSession.objects.filter(status=False, user=user).first()

        context.update({
            'list_bank_option': list_bank_option,
            'list_user_bank': list_user_bank,
            'user_online': user_online,
            'list_deposit_requests': list_deposit_requests,
            'is_session': bool(session),
            'number_failed': 0, # This seems to be static
        })
        return context

class UserLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        user_2fa, created = User2Fa.objects.get_or_create(user=user)
        if user_2fa.is_2fa_enabled:
            return redirect('cms:verify_otp')
        return redirect('cms:setup_2fa')

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('cms:index')

class ProfileView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'profile.html'
    success_url = reverse_lazy('cms:profile')
    login_url = 'cms:user_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add a success message to the context here if you want
        if 'password_change_done' in self.request.GET:
            context['success'] = 'Password changed successfully'
        return context

class Setup2FAView(LoginRequiredMixin, FormView):
    template_name = 'setup_2fa.html'
    form_class = OTPForm
    success_url = reverse_lazy('cms:index')
    login_url = 'cms:user_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_2fa, created = User2Fa.objects.get_or_create(user=self.request.user)
        if not user_2fa.otp_secret:
            user_2fa.otp_secret = pyotp.random_base32()
            user_2fa.save()

        totp = pyotp.TOTP(user_2fa.otp_secret)
        totp_uri = totp.provisioning_uri(name=self.request.user.username, issuer_name="TQA556")

        qr = qrcode.make(totp_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        context.update({
            "qr_code": qr_code_base64,
            "totp_secret": user_2fa.otp_secret
        })
        return context

    def form_valid(self, form):
        otp_code = form.cleaned_data['otp_code']
        user_2fa = User2Fa.objects.get(user=self.request.user)
        totp = pyotp.TOTP(user_2fa.otp_secret)

        if totp.verify(otp_code):
            user_2fa.is_2fa_enabled = True
            user_2fa.last_verified = timezone.now()
            user_2fa.save()
            self.request.session['is_2fa_verified'] = True
            self.request.session['2fa_verified_at'] = timezone.now().timestamp()
            return super().form_valid(form)
        else:
            form.add_error('otp_code', 'Invalid OTP')
            return self.form_invalid(form)

class VerifyOTPView(LoginRequiredMixin, FormView):
    template_name = 'verify_otp.html'
    form_class = OTPForm
    success_url = reverse_lazy('cms:index')
    login_url = 'cms:user_login'

    def form_valid(self, form):
        otp_code = form.cleaned_data['otp_code']
        user_2fa = User2Fa.objects.get(user=self.request.user)
        totp = pyotp.TOTP(user_2fa.otp_secret)

        if totp.verify(otp_code):
            self.request.session['is_2fa_verified'] = True
            self.request.session['2fa_verified_at'] = timezone.now().timestamp()
            user_2fa.last_verified = timezone.now()
            user_2fa.save()
            return super().form_valid(form)
        else:
            form.add_error('otp_code', 'Invalid OTP')
            return self.form_invalid(form)