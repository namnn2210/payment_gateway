from config.views import get_env
from pymongo import MongoClient, errors
from bank.utils import format_transaction_list, get_today_date
from django.apps import apps
from bank.utils import send_telegram_message
import re
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
import time

def mongo_connect():
    try:
        client = MongoClient(get_env("MONGODB_URL"))  # Replace with your MongoDB connection string
        db = client[get_env("MONGODB_DB")]
        client.server_info()
        return db
    except errors.ServerSelectionTimeoutError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def mongo_get_collection(collection_name):
    mongo_db = mongo_connect()
    return mongo_db[collection_name]


def get_transactions_by_account_number(account_number, transaction_type=None, status=None, date_start=None,
                                       date_end=None, order_by=None, limit_number=None, search_text=None):
    query_fields = {}
    exclude = {"_id": 0}
    if isinstance(account_number, str):
        query_fields["account_number"] = account_number
    if isinstance(account_number, list):
        query_fields["account_number"] = {"$in": account_number}
    if date_start is not None and date_end is not None:
        query_fields['transaction_date'] = {
            "$gte": date_start,
            "$lte": date_end
        }
    if transaction_type is not None and isinstance(transaction_type, str):
        query_fields["transaction_type"] = transaction_type
    if transaction_type is not None and isinstance(transaction_type, list):
        query_fields["transaction_type"] = {"$in": transaction_type}

    if status is not None:
        if status == 'Blank':
            query_fields["status"] = {"$exists": True, "$type": "null"}
        elif status != 'All':
            query_fields["status"] = status

    if search_text is not None:
        if search_text != '':
            search_text = search_text.strip()
            query_fields["$or"] = [
                {"transaction_number": {"$regex": search_text, "$options": "i"}},
                {"description": {"$regex": search_text, "$options": "i"}},
                {"account_number": {"$regex": search_text, "$options": "i"}},
                {"transfer_code": {"$regex": search_text, "$options": "i"}}
            ]
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    print('TRANSACTION QUERY: ', query_fields)
    transactions = collection.find(query_fields, exclude)
    if order_by is not None:
        transactions = transactions.sort([order_by])
    if limit_number is not None and limit_number > 0:
        transactions = transactions.limit(limit_number)
    transaction_list = [txn for txn in transactions]
    transaction_list = format_transaction_list(transaction_list)
    return transaction_list


def get_transaction_by_transaction_number(transaction_number):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    return collection.find_one({'transaction_number': transaction_number})

def get_transaction_by_description(description_substring):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    return collection.find_one({'description': {'$regex': description_substring}})


def get_new_transactions(transactions, account_number):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    existing_transactions = collection.find(
        {"account_number": str(account_number)},
        {"transaction_number": 1, "_id": 0}
    )
    existing_transaction_numbers = [txn['transaction_number'] for txn in existing_transactions]

    new_transactions = []
    for txn in transactions:
        if txn['transaction_number'] not in existing_transaction_numbers:
            new_transactions.append(txn)

    # Check if transaction is OUT and contain Z -> success
    for txn in new_transactions:
        if txn['transaction_type'] == 'OUT':
            description = txn.get('description', '')
            match = re.search(r'TQ\d{11}', description)
            payout = apps.get_model('payout', 'Payout')
            settle_payout = apps.get_model('settle_payout', 'SettlePayout')
            bank_account = apps.get_model('bank', 'BankAccount')
            if match:
                orderno = match.group()
                print("Order No: ", orderno)
                formatted_amount = '{:,.2f}'.format(txn['amount'])
                existed_payout = payout.objects.filter(memo__contains=orderno.strip()).first()
                if existed_payout:
                    print("Existed Payout: ", existed_payout)
                    if not existed_payout.status:
                        existed_payout.status = True
                        existed_payout.staging_status = True
                        existed_payout.save()
                        process_bank = bank_account.objects.filter(account_number=account_number).first()
                        alert = (
                            f'🟢🟢🟢{existed_payout.orderid}\n'
                            f'\n'
                            f'Amount: {formatted_amount} \n'
                            f'\n'
                            f'Bank name: {existed_payout.bankcode}\n'
                            f'\n'
                            f'Account name: {existed_payout.accountname}\n'
                            f'\n'
                            f'Account number: {existed_payout.accountno}\n'
                            f'\n'
                            f'Process bank: {process_bank.bank_name.name}\n'
                            f'\n'
                            f'Created by: {existed_payout.user}\n'
                            f'\n'
                            f'Done by: {existed_payout.user}\n'
                            f'\n'
                            f'Date: {existed_payout.updated_at}'
                        )
                        txn['status'] = 'Success'
                        send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_2_API_KEY'))
                    else:
                        existed_transaction = get_transaction_by_description(orderno.strip())
                        if not existed_transaction:
                            txn['status'] = 'Success'
                        else:
                            alert = (
                                f'Hi, failed\n'
                                f'\n'
                                f'Account: {txn['account_number']}'
                                f'\n'
                                f'Confirmed by order: \n'
                                f'\n'
                                f'Received amount💲: {formatted_amount} \n'
                                f'\n'
                                f'Memo: {txn['description']}\n'
                                f'\n'
                                f'Time: {txn['transaction_date']}\n'
                            )
                            send_telegram_message(alert, get_env('FAILED_PAYOUT_CHAT_ID'), get_env('226PAY_BOT'))
                else:
                    existed_settle = settle_payout.objects.filter(memo__contains=orderno.strip()).first()
                    print("Existed Settle: ", existed_settle)
                    if existed_settle and not existed_settle.status:
                        existed_settle.status = True
                        existed_settle.save()
                        process_bank = bank_account.objects.filter(account_number=account_number).first()
                        alert = (
                            f'🟢🟢🟢{existed_settle.orderid}\n'
                            f'\n'
                            f'Amount: {formatted_amount} \n'
                            f'\n'
                            f'Bank name: {existed_settle.bankcode}\n'
                            f'\n'
                            f'Account name: {existed_settle.accountname}\n'
                            f'\n'
                            f'Account number: {existed_settle.accountno}\n'
                            f'\n'
                            f'Process bank: {process_bank.bank_name.name}\n'
                            f'\n'
                            f'Created by: {existed_settle.user}\n'
                            f'\n'
                            f'Done by: {existed_settle.user}\n'
                            f'\n'
                            f'Date: {existed_settle.updated_at}'
                        )
                        txn['status'] = 'Success'
                        send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_2_API_KEY'))
                    else:
                        existed_transaction = get_transaction_by_description(orderno.strip())
                        if not existed_transaction:
                            txn['status'] = 'Success'
                        else:
                            alert = (
                                f'Hi, failed\n'
                                f'\n'
                                f'Account: {txn['account_number']}'
                                f'\n'
                                f'Received amount💲: {formatted_amount} \n'
                                f'\n'
                                f'Memo: {txn['description']}\n'
                                f'\n'
                                f'Time: {txn['transaction_date']}\n'
                            )
                            send_telegram_message(alert, get_env('FAILED_PAYOUT_CHAT_ID'), get_env('226PAY_BOT'))
    return new_transactions

def get_unprocessed_transactions(account_number):
    start_date, end_date = get_today_date()
    unprocessed_transactions = []
    query_transactions = get_transactions_by_account_number(account_number=account_number, transaction_type='IN', date_start=start_date, date_end=end_date)
    for txn in query_transactions:
        if txn['status'] == '' and txn['transfer_code'] != '':
            unprocessed_transactions.append(txn)
    return unprocessed_transactions


def update_transaction_status(account_number, transaction_number, update_fields):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    print(collection.find_one({"transaction_number": str(transaction_number), "account_number": str(account_number)}, {'_id': 0}))
    collection.update_one(
        {"transaction_number": str(transaction_number), "account_number": str(account_number)},
        {"$set": update_fields}
    )


def insert_all(transaction_list):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))

    operations = []
    for tx in transaction_list:
        operations.append(
            UpdateOne(
                {
                    "transaction_number": tx["transaction_number"],
                    "account_number": tx["account_number"]
                },
                {
                    "$setOnInsert": tx
                },
                upsert=True
            )
        )

    if operations:
        try:
            result = collection.bulk_write(operations, ordered=False)
            print(f"Inserted: {result.upserted_count}, Matched existing: {result.matched_count}")
        except BulkWriteError as bwe:
            print("Some documents caused errors (likely duplicates already exist).")
            for err in bwe.details.get("writeErrors", []):
                print(f" - Duplicated: {err.get('op', {}).get('transaction_number')}")


def get_total_amount(date_start, date_end, transaction_type):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    pipeline = [
        {
            "$match": {
                "transaction_date": {
                    "$gte": date_start,
                    "$lte": date_end
                },
                "transaction_type": {"$in":transaction_type},
                "status": "Success"
            }
        },
        {
            "$group": {
                "_id": None,  # Group all matching documents together
                "total_amount": {"$sum": "$amount"}  # Sum the `amount` field
            }
        }
    ]

    result = list(collection.aggregate(pipeline))

    # Return the total amount, or 0 if no results
    if result:
        return result[0]["total_amount"]
    else:
        return 0
