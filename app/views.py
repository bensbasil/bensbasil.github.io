from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactInquiry,Project

def home(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'projects': projects})

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # --- AVOID YOUR OWN EMAIL ---
        my_email = "bensdbasil@gmail.com" # Put your email here
        
        if email.lower() == my_email.lower():
            messages.info(request, "A message has already been received. We will be in touch shortly.")
            return redirect('contact')

        # Only save if it's NOT your email
        ContactInquiry.objects.create(
            name=name,
            email=email,
            message=message
        )

        messages.success(request, f"Thanks {name}! Your message has been sent.")
        return redirect('contact')

    return render(request, 'contact.html')