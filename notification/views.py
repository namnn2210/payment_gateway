from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse

def send_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'send_notification',
            'message': message
        }
    )

def trigger_notification(request):
    message = request.GET.get('message', 'YEU PHUONG ANH VL')
    send_notification(message)
    return JsonResponse({'status': 'Notification sent!'})