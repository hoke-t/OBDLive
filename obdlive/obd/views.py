from django.shortcuts import render

# Create your views here.

def dashboard(request):
    return render(request, 'obd/dashboard.html', {})

def dtcs(request):
    return render(request, 'obd/dtcs.html', {})
