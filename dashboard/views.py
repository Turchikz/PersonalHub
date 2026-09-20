from django.shortcuts import render

from dashboard.models import CountdownEvent

def home(request):
    events = CountdownEvent.objects.order_by('target_datetime')
    return render(request, 'dashboard/home.html', context={'events': events})