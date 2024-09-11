# middleware.py
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone

TWO_FA_EXPIRATION_TIME = 21600  # 5 minutes (can be adjusted based on your needs)

class TwoFactorAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip 2FA checks for the login and OTP verification views
        if request.path in ['/user_login', '/verify_otp', '/submit_otp']:
            return self.get_response(request)

        # Check if 2FA has been verified
        is_2fa_verified = request.session.get('is_2fa_verified', False)
        verification_time = request.session.get('2fa_verified_at')

        # If the user has verified 2FA, check the expiration
        if is_2fa_verified and verification_time:
            current_time = timezone.now().timestamp()
            elapsed_time = current_time - verification_time

            if elapsed_time > TWO_FA_EXPIRATION_TIME:
                # 2FA session has expired
                request.session['is_2fa_verified'] = False  # Invalidate the 2FA session
                return render(request, '2fa.html', {"error": "Invalid OTP"})

        # Proceed with the request
        return self.get_response(request)
