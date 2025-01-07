from config.views import get_env
from pymongo import MongoClient, errors
from bank.utils import format_transaction_list, get_today_date
from django.apps import apps
from bank.utils import send_telegram_message
import re
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
            match = re.search(r'\d{19}', description)
            if match:
                orderno = match.group()
                print("Order No: ", orderno)
                time.sleep(15)
                payout = apps.get_model('payout', 'Payout')
                existed_payout = payout.objects.filter(orderno__conta=orderno.strip(), money=txn['amount'], status=True).first()
                print("Existed payout by orderno: ", existed_payout)
                if existed_payout:
                    txn['status'] = 'Success'
                else:
                    pass
                    # formatted_description = txn.get('description', '').replace(' ', '')
                    # match = re.search(r'\d{19}', description)
                    # formatted_amount = '{:,.2f}'.format(txn['amount'])
                    # alert = (
                    #     f'Hi, failed\n'
                    #     f'\n'

                    #     f'Account: {txn['account_number']}'
                    #     f'\n'
                    #     f'Amount💲: {formatted_amount} \n'
                    #     f'\n'
                    #     f'Memo: {txn['description']}\n'
                    #     f'\n'
                    #     f'Order No: {orderno}\n'
                    #     f'\n'
                    #     f'Time: {txn['transaction_date']}\n'
                    #     f'\n'
                    #     f'Please check the transaction again'
                    # )
                    # send_telegram_message(alert, get_env('FAILED_CHAT_ID'), get_env('226PAY_BOT'))

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
    collection.insert_many(transaction_list)


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
