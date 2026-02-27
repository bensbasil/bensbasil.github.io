from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Project

def home(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'projects': projects})

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Here you could use send_mail() to send it to your inbox
        # For now, we will just show a success message
        messages.success(request, f"Thanks {name}! Your message has been sent.")
        return redirect('contact')
        
    return render(request, 'contact.html')