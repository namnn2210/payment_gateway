from config.views import get_env
from pymongo import MongoClient, errors


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
    if transaction_type is not None:
        query_fields["transaction_type"] = transaction_type
    if status is not None:
        if status != 'All':
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
    return transaction_list


def get_transaction_by_transaction_number(transaction_number):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    return collection.find_one({'transaction_number': transaction_number})


def insert_all(transaction_list):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    collection.insert_many(transaction_list)


def find_missing_transactions(transactions):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    transaction_numbers = [txn['transaction_number'] for txn in transactions]
    existing_transactions = collection.find(
        {"transaction_number": {"$in": transaction_numbers}},
        {"transaction_number": 1, "_id": 0}
    )
    existing_transaction_numbers = {txn['transaction_number'] for txn in existing_transactions}

    # Find missing transactions
    missing_transactions = [
        txn for txn in transactions
        if txn['transaction_number'] not in existing_transaction_numbers
    ]
    return missing_transactions


def update_transaction_status(account_number, transfer_code, orderid, scode, incomingorderid, status):
    collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
    update_fields = {
        "orderid": orderid,
        "scode": scode,
        "incomingorderid": incomingorderid,
        "status": status,
    }
    collection.update_one(
        {"transfer_code": transfer_code, "account_number": account_number},
        {"$set": update_fields}
    )
