from config.views import get_env
from partner.models import CID
import hashlib
import requests
import logging

logger = logging.getLogger('django')


def create_deposit_order(transaction, cid):
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        # key_df = pd.read_csv(get_env('MID_KEY'))
        scode = cid.name
        cardtype = cid.cardtype
        key = cid.key

        payeeaccountno = str(transaction['account_number'])
        amount = f'{str(transaction['amount'])}.00'

        transfercode = transaction['transfer_code']
        payername = 'NA'
        payeraccountno = str(transaction['account_number'])[-4:]

        hashid = str(transaction['transaction_number'])

        # Create the sign string
        sign_string = f"{scode}|{payeeaccountno}|{amount}|{transfercode}|{payername}|{payeraccountno}|{hashid}|{cardtype}:{key}"
        # Generate MD5 signature
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

        payload = {
            'scode': scode,
            'payeeaccountno': payeeaccountno,
            'cardtype': cardtype,
            'amount': amount,
            'payername': payername,
            'payeraccountno': payeraccountno,
            'transfercode': transfercode,
            'hashid': hashid,
            'sign': sign,
        }

        print(payload)

        response = requests.post(get_env('DEPOSIT_URL'), data=payload, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            logger.info(response_data)
            return response_data
        else:
            return None

    except Exception as e:
        return None


def create_multiple_deposit_order(transactions, cid):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payloads = []
    for transaction in transactions:
        # key_df = pd.read_csv(get_env('MID_KEY'))
        scode = cid.name
        cardtype = cid.cardtype
        key = cid.key

        payeeaccountno = str(transaction['account_number'])
        amount = f'{str(transaction['amount'])}.00'

        transfercode = transaction['transfer_code']
        payername = 'NA'
        payeraccountno = str(transaction['account_number'])[-4:]

        hashid = str(transaction['transaction_number'])

        # Create the sign string
        sign_string = f"{scode}|{payeeaccountno}|{amount}|{transfercode}|{payername}|{payeraccountno}|{hashid}|{cardtype}:{key}"
        # Generate MD5 signature
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

        payloads.append({
            'scode': scode,
            'payeeaccountno': payeeaccountno,
            'cardtype': cardtype,
            'amount': amount,
            'payername': payername,
            'payeraccountno': payeraccountno,
            'transfercode': transfercode,
            'hashid': hashid,
            'sign': sign,
        })

    try:
        response = requests.post(get_env('DEPOSIT_URL'), json=payloads, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            logger.info(response_data)
            return response_data
        else:
            return None
    except Exception as e:
        return None


def update_status_request(payout, status='S'):
    cid = CID.objects.filter(name=payout.scode).first()

    key = cid.key
    sign_string = f"{payout.scode}|{payout.orderno}:{key}"
    # Generate MD5 signature
    sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    request_body = {
        "scode": payout.scode,
        "data": [
            {
                "orderno": payout.orderno,
                "amount": f'{payout.money}.00',
                "payerbankname": payout.partner_bankcode,
                "payeraccountno": "2017241",
                "payeraccountname": "TQA556",
                "status": status
            }
        ],
        "sign": sign
    }
    logger.info(f'update resquest body:{request_body}')
    response = requests.post('https://p2p.jzc899.com/service/withdraw_confirm.aspx', json=request_body)
    logger.info(f'response:{response.text}')

    if response.status_code == 200:
        response_data = response.json()
        logger.info(f'update resquest response:{response_data}')
        if response_data['errcode'] == '00':
            update_success_list = response_data.get('updatescuuesslist')
            update_failed_list = response_data.get('updateafaillist')
            if len(update_success_list) > 0:
                for item in update_success_list:
                    if item == payout.orderno:
                        return True
            else:
                for item in update_failed_list:
                    if item['errormsg'] == 'Orderno status completed.' and item['orderno'] == payout.orderno:
                        return True
    return False
