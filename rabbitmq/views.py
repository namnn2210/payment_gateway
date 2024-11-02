import pika
import os
import json
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bank.models import BankAccount


def send_notification(amount, account_number, transaction_date):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=f'noti_{account_number}')
    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps({'amount':amount,'transaction_date':transaction_date}))
    connection.close()


@login_required(login_url='user_login')
def get_notifications(request):
    # Fetch all active bank accounts for the user
    if request.user.is_superuser:
        bank_accounts = BankAccount.objects.filter(status=True)
    else:
        bank_accounts = BankAccount.objects.filter(user=request.user, status=True)

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    recent_notifications = []

    # Iterate through each bank account's queue
    for account in bank_accounts:
        queue_name = f'noti_{account.account_number}'
        try:
            method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)
        except Exception as e:
            print('Error sending notification:', str(e))
            continue

        # Process the message if it exists
        if body:
            transaction = json.loads(body.decode('utf-8'))
            print('===========', transaction)
            transaction_date = timezone.datetime.fromisoformat(transaction.get('transaction_date'))

            # Check if the transaction is older than 2 minutes
            if timezone.now() - transaction_date >= timedelta(minutes=2):
                recent_notifications.append(transaction)

    # Close the RabbitMQ connection
    connection.close()

    # Return the list of recent notifications
    return JsonResponse({"notifications": recent_notifications})



