from django.urls import path

from . import views

urlpatterns = [
    path('', views.poll, name='poll'),

]