from django.shortcuts import redirect
from django.utils import timezone
from cms.models import User2Fa

TWO_FA_EXPIRATION_TIME = 21600  # 6 hours

class TwoFactorAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(request.path)
        if request.path in ['/user_login', '/verify_otp', '/en/setup_2fa','/vi/setup_2fa']:
            return self.get_response(request)

        if request.user.is_authenticated:
            user_2fa = User2Fa.objects.filter(user=request.user).first()
            if user_2fa:
                if not user_2fa.is_2fa_enabled:
                    return redirect('setup_2fa')
                is_2fa_verified = request.session.get('is_2fa_verified', False)
                verification_time = request.session.get('2fa_verified_at')
                if is_2fa_verified and verification_time:
                    current_time = timezone.now().timestamp()
                    elapsed_time = current_time - verification_time
                    if elapsed_time > TWO_FA_EXPIRATION_TIME:
                        request.session['is_2fa_verified'] = False
                        return redirect('verify_otp')
                if not is_2fa_verified:
                    return redirect('verify_otp')
        return self.get_response(request)