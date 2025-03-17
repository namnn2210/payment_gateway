from django.http import JsonResponse
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API documentation root view.
    """
    return JsonResponse({
        'auth': {
            'token_obtain': request.build_absolute_uri(reverse('token_obtain_pair')),
            'token_refresh': request.build_absolute_uri(reverse('token_refresh')),
            'token_verify': request.build_absolute_uri(reverse('token_verify')),
        },
        'bank': {
            'banks': request.build_absolute_uri('/api/bank/banks/'),
            'accounts': request.build_absolute_uri('/api/bank/accounts/'),
        },
        'payout': {
            'payouts': request.build_absolute_uri('/api/payout/payouts/'),
            'timelines': request.build_absolute_uri('/api/payout/timelines/'),
            'user_timelines': request.build_absolute_uri('/api/payout/user-timelines/'),
            'balance_timelines': request.build_absolute_uri('/api/payout/balance-timelines/'),
        },
        'settle': {
            'settle_payouts': request.build_absolute_uri('/api/settle/payouts/'),
        },
        'acb': {
            'accounts': request.build_absolute_uri('/api/acb/accounts/'),
        },
        'partner': {
            'partners': request.build_absolute_uri('/api/partner/partners/'),
        },
        'employee': {
            'employees': request.build_absolute_uri('/api/employee/employees/'),
            'sessions': request.build_absolute_uri('/api/employee/sessions/'),
        },
    }) 