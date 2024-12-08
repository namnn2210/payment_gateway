import logging
from mb.views import mb_balance, mb_transactions, mb_login
from acb.views import acb_transactions, acb_balance, acb_login
from vietin.views import vietin_login, vietin_balance, vietin_transactions
from tech.views import tech_login, tech_balance, tech_transactions
from bank.utils import send_telegram_message, find_substring
from bank.views import update_amount_by_date, update_transaction_history_status
from bank.models import BankAccount
from partner.views import create_deposit_order
from partner.models import CID
from datetime import datetime
from django.utils import timezone
from config.views import get_env
from mongodb.views import get_transactions_by_account_number, insert_all, find_missing_transactions
import pytz

logger = logging.getLogger('django')


def get_balance(bank):
    error_count = 0

    print('Fetching bank balance: ', bank.account_name, bank.account_number, bank.bank_name, bank.username,
          bank.password)
    # Get balance
    if bank.bank_name.name == 'MB':
        bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == "Techcombank":
        bank_balance = tech_balance(bank.username, bank.password, bank.account_number)
    else:
        bank_balance = None
    while bank_balance is None:
        print('Error fetching bank balance, try to login')
        error_count += 1
        print('Retry logging in: ', error_count)
        if error_count > 3:
            alert = (
                f'🔴 - LỖI HỆ THỐNG\n'
                f'Dữ liệu tài khoản: {bank.account_number} trống\n'
                f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
            )
            send_telegram_message(alert, get_env('MONITORING_CHAT_ID'), get_env('MONITORING_BOT_API_KEY'))
            return

        bank_logged_in = None

        if bank.bank_name.name == 'MB':
            bank_logged_in = mb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'ACB':
            bank_logged_in = acb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Vietinbank':
            bank_logged_in = vietin_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Techcombank':
            bank_logged_in = tech_login(bank.username, bank.password, bank.account_number)

        if bank_logged_in:
            if bank.bank_name.name == 'MB':
                bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'ACB':
                bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Vietinbank':
                bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Techcombank':
                bank_balance = tech_balance(bank.username, bank.password, bank.account_number)
            else:
                bank_balance = None

    if bank_balance:
        if int(bank_balance) != int(bank.balance):
            bank.balance = bank_balance
            bank.updated_at = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
            bank.save()
            print('Update for bank: %s. Updated at %s' % (
                bank.account_number, timezone.now().strftime('%Y-%m-%d %H:%M:%S')))


            get_transaction(bank)

        else:
            pass
    elif bank_balance is None:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lấy số dư tài khoản {bank.account_number} - {bank.bank_name.name} không thành công\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        )
        send_telegram_message(alert, get_env('MONITORING_CHAT_ID'), get_env('MONITORING_BOT_API_KEY'))


def get_transaction(bank):
    current_transactions = get_transactions_by_account_number(bank.account_number)
    if bank.bank_name.name == 'MB':
        new_transactions = mb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        new_transactions = acb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        new_transactions = vietin_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Techcombank':
        new_transactions = tech_transactions(bank.username, bank.password, bank.account_number)
    else:
        new_transactions = None

    if not new_transactions:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lỗi lấy lịch sử giao dịch từ {bank.account_number} - {bank.bank_name.name} empty\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        )
        send_telegram_message(alert, get_env('MONITORING_CHAT_ID'), get_env('MONITORING_BOT_API_KEY'))

    if not current_transactions:
        transaction_dicts = [txn for txn in new_transactions]
        insert_all(transaction_list=transaction_dicts)
    else:
        different_transactions = find_missing_transactions(new_transactions)
        transaction_dicts = [txn for txn in different_transactions]
        insert_all(transaction_list=transaction_dicts)
        if different_transactions:
            print("=======", different_transactions)
            for row in different_transactions:
                bank_account = BankAccount.objects.filter(account_number=str(row.account_number)).first()
                if not datetime.strptime(row.transaction_date, '%d/%m/%Y %H:%M:%S').date() >= timezone.now().date():
                    continue
                if row.transaction_type == 'IN':
                    formatted_amount = '{:,.2f}'.format(row['amount'])
                    memo_transfer_check = 'W' + bank_account.account_name
                    memo_deposit_check = 'D' + bank_account.account_name
                    if memo_transfer_check in row.description or memo_deposit_check in row.description:
                        continue
                    success = False
                    reported = False
                    if bank_account:
                        cids = CID.objects.filter(status=True)
                        for item in cids:
                            logger.info(item.name)
                            result = create_deposit_order(row, item)
                            logger.info(result)
                            if result:
                                if result['msg'] == 'transfercode is null':
                                    update_transaction_history_status(row.account_number, row.transfer_code, '',
                                                                      '', '', 'Failed')
                                    alert = (
                                        f'Hi, failed\n'
                                        f'\n'
                                        f'Account: {row.account_number}'
                                        f'\n'
                                        f'Confirmed by order: \n'
                                        f'\n'
                                        f'Received amount💲: {formatted_amount} \n'
                                        f'\n'
                                        f'Memo: {row.description}\n'
                                        f'\n'
                                        f'Code: {find_substring(row.description)}\n'
                                        f'\n'
                                        f'Time: {row.transaction_date}\n'
                                        f'\n'
                                        f'Reason of not be credited: No transfer code!!!'
                                    )
                                    send_telegram_message(alert, get_env('FAILED_CHAT_ID'),
                                                          get_env('226PAY_BOT'))
                                    reported = True
                                    break

                                if result['prc'] == '1' and result['errcode'] == '00' and result['msg'] == "SUCCESS":
                                    if result['orderno'] == '':
                                        continue
                                    else:
                                        update_transaction_history_status(row.account_number,
                                                                          row.transfer_code, result['orderid'],
                                                                          result['scode'], result['incomingorderid'],
                                                                          'Success')
                                        alert = (
                                            f'🟩🟩🟩 Success! CID: {item.name}\n'
                                            f'\n'
                                            f'Account: {row.account_number}'
                                            f'\n'
                                            f'Confirmed by order: {result['incomingorderid']}\n'
                                            f'\n'
                                            f'Received amount💲: {formatted_amount} \n'
                                            f'\n'
                                            f'Memo: {row.description}\n'
                                            f'\n'
                                            f'Order ID: {result['orderid']}\n'
                                            f'\n'
                                            f'Code: {find_substring(row.description)}\n'
                                            f'\n'
                                            f'Time: {row.transaction_date}\n'
                                        )
                                        send_telegram_message(alert, get_env('TRANSACTION_CHAT_ID'),
                                                              get_env('TRANSACTION_BOT_API_KEY'))
                                        update_amount_by_date('IN', row['amount'])
                                        success = True
                                        break
                                else:
                                    continue
                            else:
                                continue
                        if not success and not reported:
                            update_transaction_history_status(row.account_number, row.transfer_code, '', '', '',
                                                              'Failed')
                            alert = (
                                f'Hi, failed\n'
                                f'\n'
                                f'Account: {row.account_number}'
                                f'\n'
                                f'Confirmed by order: \n'
                                f'\n'
                                f'Received amount💲: {formatted_amount} \n'
                                f'\n'
                                f'Memo: {row.description}\n'
                                f'\n'
                                f'Code: {find_substring(row.description)}\n'
                                f'\n'
                                f'Time: {row.transaction_date}\n'
                                f'\n'
                                f'Reason of not be credited: Order not found!!!'
                            )
                            bank_accounts = BankAccount.objects.filter(status=True)
                            set_name = set([bank_account.account_name for bank_account in bank_accounts])
                            internal = False
                            for name in set_name:
                                first_name = name.split(' ')[-1]
                                memo_transfer_check = 'W' + first_name
                                memo_deposit_check = 'D' + first_name
                                if memo_transfer_check in row.description or memo_deposit_check in row.description:
                                    internal = True
                                    break
                            if not internal and bank.bank_type == 'IN':
                                send_telegram_message(alert, get_env('FAILED_CHAT_ID'),
                                                      get_env('226PAY_BOT'))
                else:
                    transaction_type = '-'
                    transaction_color = '🔴'  # Red circle emoji for OUT transactions
                    formatted_amount = '{:,.2f}'.format(row.amount)

                    alert = (
                        f'💰 {transaction_color} {transaction_type}{formatted_amount} \n'
                        f'\n'
                        f'Nội dung: {row.description}\n'
                        f'\n'
                        f'🏦 {bank.account_number} - {bank.account_name}\n'
                        f'\n'
                        f'🕒 {row.transaction_date}'
                    )

                    bank_accounts = BankAccount.objects.filter(status=True)
                    set_name = set([bank_account.account_name for bank_account in bank_accounts])
                    internal = False
                    for name in set_name:
                        first_name = name.split(' ')[-1]
                        memo_transfer_check = 'W' + first_name
                        memo_deposit_check = 'D' + first_name
                        if memo_transfer_check in row.description or memo_deposit_check in row.description and bank.bank_type == 'OUT':
                            send_telegram_message(alert, get_env('INTERNAL_CHAT_ID'),
                                                  get_env('TRANSACTION_BOT_API_KEY'))
                            internal = True
                            break
                    if not internal:
                        send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_API_KEY'))
            print('Update transactions for bank: %s. Updated at %s' % (
            bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            pass
