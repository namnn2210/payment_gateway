from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import EmployeeDeposit, EmployeeWorkingSession
from .forms import DepositForm
from bank.models import BankAccount
from django.utils import timezone

class EmployeeDepositView(LoginRequiredMixin, FormMixin, ListView):
    model = EmployeeDeposit
    template_name = 'employee/deposit.html'
    context_object_name = 'list_deposit_requests'
    form_class = DepositForm
    success_url = reverse_lazy('employee:employee_deposit')
    login_url = 'cms:user_login'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return EmployeeDeposit.objects.all().order_by('-created_at')
        return EmployeeDeposit.objects.filter(user=self.request.user).order_by('-created_at')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        bank = form.cleaned_data['bank']
        EmployeeDeposit.objects.create(
            user=self.request.user,
            amount=form.cleaned_data['deposit'],
            bankname=bank.bank_name,
            accountno=bank.account_number,
            accountname=bank.account_name,
            bankcode=bank.bank_name.bankcode
        )
        return super().form_valid(form)

class UpdateDepositAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            deposit = EmployeeDeposit.objects.get(id=request.data.get('id'))
            deposit.status = True
            deposit.save()
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
        except EmployeeDeposit.DoesNotExist:
            return Response({'message': 'Deposit not found', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': str(e), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteDepositAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            deposit = EmployeeDeposit.objects.get(id=request.data.get('id'))
            deposit.delete()
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
        except EmployeeDeposit.DoesNotExist:
            return Response({'message': 'Deposit not found', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': str(e), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeeSessionAPIView(APIView):
    def post(self, request, session_type, *args, **kwargs):
        undone_session = EmployeeWorkingSession.objects.filter(user=request.user, status=False).first()

        if session_type == 'start':
            if undone_session:
                return Response({'message': 'Đang trong phiên làm việc. Không thể bắt đầu', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeWorkingSession.objects.create(user=request.user, start_time=timezone.now())
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

        elif session_type == 'end':
            if undone_session:
                # The original code had a reference to an undefined `end_balance`
                # I'm setting it to 0 as a placeholder. You might need to adjust this.
                undone_session.end_balance = 0 
                undone_session.end_time = timezone.now()
                undone_session.status = True
                undone_session.save()
                return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
            return Response({'message': 'Không có phiên làm việc nào để kết thúc', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Trạng thái không hợp lệ', 'success': False}, status=status.HTTP_400_BAD_REQUEST)