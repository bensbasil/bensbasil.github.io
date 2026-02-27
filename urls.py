from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),          # Matches http://127.0.0.1:8000/
    path('contact/', views.contact_view, name='contact'), # Matches http://127.0.0.1:8000/contact/
]