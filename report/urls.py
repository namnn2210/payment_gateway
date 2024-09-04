from django.urls import path
from .views import report,report_payout_by_user,report_all
urlpatterns = [
    path('report', report, name='report'),
    path('report_payout_by_user', report_payout_by_user, name='report_payout_by_user'),
    path('report_all', report_all, name='report_all')
]