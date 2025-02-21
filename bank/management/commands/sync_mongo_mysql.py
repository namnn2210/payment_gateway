from django.core.management.base import BaseCommand
from django.db import IntegrityError
from mongodb.views import mongo_get_collection
from config.views import get_env
from transaction.models import TransactionHistory

class Command(BaseCommand):
    help = 'Sync MongoDB to MySQL'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting syncing MongoDB...'))

        collection = mongo_get_collection(get_env("MONGODB_COLLECTION_TRANSACTION"))
        transactions = collection.find()

        batch = []  # List to store transactions for bulk insert
        for transaction in transactions:
            try:
                new_transaction = TransactionHistory(
                    transaction_number=transaction['transaction_number'],
                    created_at=transaction['transaction_date'],
                    transaction_type=transaction['transaction_type'],
                    account_number=transaction['account_number'],
                    description=transaction['description'],
                    transfer_code=transaction.get('transfer_code'),  # Use .get() to avoid KeyError
                    status=transaction['status'],
                    amount=transaction['amount'],
                    note=transaction.get('note'),
                    orderid=transaction.get('orderid'),
                    scode=transaction.get('scode'),
                    incomingorderid=transaction.get('incomingorderid'),
                )
                batch.append(new_transaction)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Skipping transaction {transaction.get('transaction_number', 'UNKNOWN')}: {str(e)}"))

        # Bulk insert to improve performance and skip errors
        if batch:
            try:
                TransactionHistory.objects.bulk_create(batch, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f"Successfully inserted {len(batch)} transactions."))
            except IntegrityError as e:
                self.stderr.write(self.style.ERROR(f"Bulk insert error: {str(e)}"))

        self.stdout.write(self.style.SUCCESS('Syncing complete.'))
