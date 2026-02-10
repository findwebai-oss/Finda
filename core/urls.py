from django.urls import path
from .views import home, search_ajax

urlpatterns = [
    path("", home, name="home"),
    path("search_ajax/", search_ajax, name="search_ajax"),
]
