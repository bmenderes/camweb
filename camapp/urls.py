from django.contrib import admin
from django.urls import path
from camapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("generate/", views.generate, name="generate"),
    path("export_csv/", views.export_csv, name="export_csv"),
]
