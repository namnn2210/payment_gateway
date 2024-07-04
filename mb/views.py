from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.http import JsonResponse
import string
import random
import requests
import json
import hashlib
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

headers = {
    'Host':'online.mbbank.com.vn',
    'Content-Type':'application/json; charset=UTF-8',
    'User-Agent':'MB%20Bank/2 CFNetwork/1331.0.3 Darwin/21.4.0',
    'Connection':'keep-alive',
    'Accept':'application/json',
    'Accept-Language':'vi-VN,vi;q=0.9',
    'Authorization':'Basic QURNSU46QURNSU4=',
    'Accept-Encoding':'gzip, deflate, br'
}
captcha_key = ''
account = ''
timeout = 15
captcha_code = ''
captcha_image = ''
session_id = ''
cust = ''
client = ''
        

# Create your views here.
@csrf_exempt
def mb_login(request):
    global captcha_image
    if request.method == 'POST':
        body_request_json = json.loads(request.body)
        captcha_data = get_captcha()
        if captcha_data:
            captcha_image = captcha_data.get('imageString')
            if solve_captcha():
                body = {
                    'userId':body_request_json.get('username'),
                    'password':hashlib.md5(body_request_json.get('password').encode()).hexdigest()
                }
                response = requests.post('https://online.mbbank.com.vn/retail_web/internetbanking/doLogin', json=body, timeout=timeout)
                if response.status_code == 200:
                    print('dologin', response.json())
                    return JsonResponse({'status': 200, 'message': 'Success'})
    return JsonResponse({'status': 405, 'message': 'Error'})

@csrf_exempt
def transactions(request):
    pass

@csrf_exempt
def balance(request):
    pass

@csrf_exempt
def transfer(request):
    pass

def get_captcha():
    body = {
        'sessionId':"",
        'refNo': datetime.now().strftime('%Y%m%d%H%M%S'),
        'deviceIdCommon': generate_imei()
    }
    response = requests.post('https://online.mbbank.com.vn/retail-web-internetbankingms/getCaptchaImage', headers=headers, json=body)
    if response.status_code == 200:
        return response.json()
    return None

def solve_captcha():
    global captcha_image, captcha_code
    data_post = {
        'username':os.environ.get('CAPTCHA_USERNAME'),
        'api_key':os.environ.get('CAPTCHA_API_KEY'),
        'img_base64':captcha_image
    }
    headers = {
            'Content-Type': 'application/json'
        }
    response = requests.post(
        url="https://dichvudark.vn/api/captcha/mbbank",
        headers=headers,
        data=json.dumps(data_post),
        timeout=30,
        allow_redirects=True
    )
    if response.status_code == 200:
        print('solve catpcha' ,response.json())
        # captcha_code = response.json()['data']['captcha']
        return True
    return False

def generate_random_string(length=20):
    # Generates a random string of the specified length from the given characters
    # characters = string.digits + string.ascii_lowercase + string.ascii_uppercase
    characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    character_length = len(characters)
    random_string = ''
    for i in range(0, length):
        random_string += characters[random.randint(0, character_length - 1)]
    return random_string

def generate_imei():
    # Concatenates random strings with specified lengths separated by hyphens
    return f"{generate_random_string(8)}-{generate_random_string(4)}-{generate_random_string(4)}-{generate_random_string(4)}-{generate_random_string(12)}"