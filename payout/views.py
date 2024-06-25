from django.shortcuts import render
from .models import Payout
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
# Create your views here.
def list_payout(request):
    if request.user.is_superuser:
        list_payout = Payout.objects.all()
    else:
        list_payout = Payout.objects.filter(user=request.user)
    paginator = Paginator(list_payout, 10)  # Show 10 items per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    items = [model_to_dict(item) for item in page_obj]

    return render(request, 'payout.html', {
        'page_obj': page_obj,
        'items_json': json.dumps(items),
    })

def search_payout(request):
    return render(request=request, template_name='payout_history.html')

@csrf_exempt
@require_POST
def update_payout(request):
    # if request.method == 'POST':
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        payout = get_object_or_404(Payout, id=payout_id)
        payout.status = True  # Assuming 'True' marks the payout as done
        payout.save()
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': 'Done','success': False})