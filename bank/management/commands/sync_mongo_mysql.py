from django.core.management.base import BaseCommand

from bank.utils import Transaction
from mongodb.views import mongo_get_collection
from config.views import get_env
from transaction.models import TransactionHistory

class Command(BaseCommand):
    help = 'Sync mongodb to mysql'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting syncing mongodb...'))

        collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
        transactions = collection.find()[:5]
        for transaction in transactions:

            new_transaction = TransactionHistory(
                transaction_number=transaction['transaction_number'],
                created_at=transaction['transaction_date'],
                transaction_type=transaction['transaction_type'],
                account_number=transaction['account_number'],
                description=transaction['description'],
                transfer_code=transaction['transfer_code'] if transaction['transfer_code'] else None,
                status=transaction['status'],
                amount=transaction['amount'],
                note=transaction['note'] if transaction['note'] else None,
                orderid=transaction['orderid'] if transaction['orderid'] else None,
                scode=transaction['scode'] if transaction['scode'] else None ,
                incomingorderid=transaction['incomingorderid'] if transaction['incomingorderid'] else None,
            )
            new_transaction.save()
