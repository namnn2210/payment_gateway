from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from bank.models import BankAccount, Bank
from employee.models import EmployeeDeposit
from django.core.paginator import Paginator
import requests

CURRENCY_SYMBOLS = {
    'USD': '$',
    'VND': '₫',
    'JPY': '¥',
    'KRW': '₩'
}
FIAT_CURRENCIES = ['USD', 'VND', 'JPY', 'KRW']

# Create your views here.
@login_required(login_url='user_login')
def index(request):
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
    
        
    return render(request=request, template_name='index.html', context={'list_user_bank':list_user_bank,'list_deposit_requests':list_deposit_requests,'list_bank_option':list_bank_option})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index') 
        else:
            return render(request=request, template_name='login.html', context={'error': 'Invalid username or password. Contact admin for support'})
    return render(request=request, template_name='login.html')


def convert(request):
    if request.method == "POST":
        crypto = request.POST.get('crypto')
        currency = request.POST.get('currency')
        amount = float(request.POST.get('amount', 1))  # Get amount and convert to float

        # If both the source and target are fiat currencies, use ExchangeRateAPI
        if crypto in FIAT_CURRENCIES and currency in FIAT_CURRENCIES:
            # ExchangeRateAPI URL
            url = f"https://v6.exchangerate-api.com/v6/8433fd7e3b40361d61f15300/pair/{crypto}/{currency}/{amount}"
            # headers = {'apikey': '8433fd7e3b40361d61f15300'}

            try:
                response = requests.get(url)
                data = response.json()

                if data['result'] == 'success':
                    # Extract the conversion result and format it
                    converted_amount = data['conversion_result']
                    formatted_converted_amount = f"{converted_amount:,.2f}"

                    # Reverse conversion rate (1 unit of the target currency to the source currency)
                    conversion_rate = data['conversion_rate']
                    reverse_conversion_rate = 1 / conversion_rate
                    formatted_reverse_rate = f"{reverse_conversion_rate:,.5f}"

                    # Get the currency symbols
                    source_symbol = CURRENCY_SYMBOLS.get(crypto, '')
                    target_symbol = CURRENCY_SYMBOLS.get(currency, '')

                    # Format the result text
                    result_text = (
                        f"{amount:,.2f} {source_symbol} {crypto} = {formatted_converted_amount} {target_symbol} {currency}<br>"
                        f"1 {currency} = {formatted_reverse_rate} {crypto}"
                    )

                    return JsonResponse({'result': result_text}, status=200)
                else:
                    return JsonResponse({'error': 'Failed to fetch data from ExchangeRateAPI'}, status=500)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        # Otherwise, use CoinMarketCap for cryptocurrency conversions
        else:
            url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={crypto}&convert={currency}"
            headers = {'X-CMC_PRO_API_KEY': 'd32e9043-4a06-4f5e-851d-96b5ba015cb5'}

            try:
                response = requests.get(url, headers=headers)
                data = response.json()

                if response.status_code == 200:
                    price = data['data'][crypto]['quote'][currency]['price']
                    converted_amount = price * amount
                    formatted_converted_amount = f"{converted_amount:,.2f}"

                    reverse_conversion_rate = 1 / price
                    formatted_reverse_rate = f"{reverse_conversion_rate:,.5f}"

                    # Get the currency symbols
                    target_symbol = CURRENCY_SYMBOLS.get(currency, '')
                    crypto_symbol = crypto.upper()

                    # Format the result text
                    result_text = (
                        f"{amount:,.2f} {crypto_symbol} = {formatted_converted_amount} {target_symbol}<br>"
                        f"1 {currency} = {formatted_reverse_rate} {crypto_symbol}"
                    )

                    return JsonResponse({'result': result_text}, status=200)
                else:
                    return JsonResponse({'error': 'Failed to fetch data from CoinMarketCap'},
                                        status=response.status_code)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

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

def user_logout(request):
    logout(request)
    return redirect('index')