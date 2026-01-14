"""
URL configuration for biblioteca project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",views.dashboard, name="dashboard"),
    path("libros/", views.libros_list, name="libros_list"),
    path("libros/exportar/", views.libros_export, name="libros_export"),
    path("libros/nuevo/", views.libro_create, name="libro_create"),
    path("libros/<int:pk>/eliminar", views.libro_eliminar, name="libro_eliminar"),
    path("prestamos/", views.prestamos_list, name="prestamos_list"),
    path("prestamos/nuevo/", views.prestamo_create, name="prestamo_create"),
    path("prestamos/<int:pk>/devolver/", views.prestamo_devolver, name="prestamo_devolver"),
    path("prestamos/<int:pk>/renovar/", views.prestamo_renovar, name="prestamo_renovar"),
    path("prestamos/<int:pk>/eliminar/", views.prestamo_eliminar, name="prestamo_eliminar"),
    path("categorias/create/", views.categoria_create_ajax, name="categoria_create_ajax"),
    path("categorias/<int:pk>/delete/", views.categoria_delete, name="categoria_delete"),
]
