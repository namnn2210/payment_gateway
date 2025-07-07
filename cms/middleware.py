from django.shortcuts import redirect
from django.utils import timezone
from cms.models import User2Fa
from django.urls import reverse, resolve, Resolver404

TWO_FA_EXPIRATION_TIME = 28800  # 6 hours

class TwoFactorAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude admin and static files
        if request.path.startswith(('/admin', '/static/', '/media/')):
            return self.get_response(request)

        # Get the URL names for 2FA related pages
        login_url_name = 'user_login'
        verify_otp_url_name = 'verify_otp'
        setup_2fa_url_name = 'setup_2fa'

        # Get the resolved URL name for the current request
        resolved_url_name = None
        try:
            resolved_url_name = resolve(request.path_info).url_name
        except Resolver404:
            pass # URL not found, let Django handle 404 later

        # Check if the current request is for one of the 2FA related pages
        # This is crucial to prevent redirect loops on these pages themselves.
        if resolved_url_name in [login_url_name, verify_otp_url_name, setup_2fa_url_name]:
            return self.get_response(request)

        # If user is not authenticated, let Django's default auth handle it.
        if not request.user.is_authenticated:
            return self.get_response(request)

        # User is authenticated. Now check 2FA status.
        user_2fa = User2Fa.objects.filter(user=request.user).first()

        if user_2fa:
            # 2FA is enabled for this user
            if user_2fa.is_2fa_enabled:
                is_2fa_verified = request.session.get('is_2fa_verified', False)
                verification_time = request.session.get('2fa_verified_at')

                # Check if 2FA verification has expired
                if is_2fa_verified and verification_time:
                    current_time = timezone.now().timestamp()
                    elapsed_time = current_time - verification_time
                    if elapsed_time > TWO_FA_EXPIRATION_TIME:
                        request.session['is_2fa_verified'] = False # Mark as unverified
                        return redirect('cms:verify_otp') # Redirect to verify_otp if expired

                # If not verified (or just expired and marked unverified above), redirect to verify_otp
                if not is_2fa_verified:
                    return redirect('cms:verify_otp')
            # 2FA is not enabled for this user, redirect to setup
            else:
                return redirect('cms:setup_2fa')
        else:
            # No User2Fa object for this user, means 2FA is not set up, redirect to setup
            return redirect('cms:setup_2fa')

        # If none of the above conditions triggered a redirect, proceed with the request
        return self.get_response(request)
