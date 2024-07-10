from django.shortcuts import render
from .models import Payout
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from bank.utils import send_telegram_message
from dotenv import load_dotenv
import os
import json

load_dotenv()
# Create your views here.
def list_payout(request):
    
    bank_data = json.load(open('bank.json', encoding='utf-8'))
    
    if request.user.is_superuser:
        list_payout = Payout.objects.all().order_by('-status')
    else:
        list_payout = Payout.objects.filter(user=request.user).order_by('-status')
    # paginator = Paginator(list_payout, 10)  # Show 10 items per page

    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    items = [model_to_dict(item) for item in list_payout]

    return render(request, 'payout.html', {
        'list_payout': list_payout, 'items_json':items, 'bank_data':bank_data})

def search_payout(request):
    return render(request=request, template_name='payout_history.html')

@method_decorator(csrf_exempt, name='dispatch')
class AddPayoutView(View):
    def post(self, request, *args, **kwargs):
        decoded_str = request.body.decode('utf-8')
        data = json.loads(decoded_str)
        scode = data.get('scode')
        orderid = data.get('orderid')
        money = data.get('money')
        accountno = data.get('accountno')
        accountname = data.get('accountname')
        bankcode = data.get('bankcode')
        
        # Check if any bank_account with the same type is ON
        existed_bank_account = Payout.objects.filter(
            orderid=orderid).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Existed payout. Please try again'})

        #Process the data and save to the database
    
        payout = Payout.objects.create(
            user=request.user,
            scode=scode,
            orderno=orderid,
            orderid=orderid,
            money=int(float(money)),
            accountno=accountno,
            accountname=accountname,
            bankcode=bankcode,
            is_auto=False,
            is_cancel=False,
            is_report=False,
        )
        payout.save()
        return JsonResponse({'status': 200, 'message': 'Bank added successfully'})


@csrf_exempt
@require_POST
def update_payout(request):
    # if request.method == 'POST':
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        payout = get_object_or_404(Payout, id=payout_id)
        payout.status = True  # Assuming 'True' marks the payout as done
        payout.save()
        formatted_amount = '{:,.2f}'.format(payout.money)
        alert = (
                f'Order ID: {payout.orderid}\n'
                f'Amount: {formatted_amount} VND\n'
                f'Bank name: {payout.bankcode}\n'
                f'Account name: {payout.accountname}\n'
                f'Account number: {payout.accountno}'
            )
        send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': 'Done','success': False})