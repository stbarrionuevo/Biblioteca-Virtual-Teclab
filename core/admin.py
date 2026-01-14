from django.contrib import admin
from .models import Categoria, Titulo, Ejemplar, Prestamo

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ["nombre"]
    list_display = ["id","nombre"]
    ordering = ["nombre"]

@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    list_display= ("id","titulo","autor", "tipo", "editorial","anio")
    list_filter = ("tipo","editorial","anio","categorias")
    search_fields = ("titulo", "autor","isbn")
    filter_horizontal = ["categorias"]
    ordering=["titulo"]

@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display=["id","titulo","codigo","estado"]
    list_filter=["estado","titulo__tipo"]
    search_fields=["codigo","titulo__titulo"]
    ordering=["titulo__titulo","id"]


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ["id", "ejemplar", "alumno_nombre", "alumno_dni", "fecha_prestamo", "vence", "estado"]
    list_filter = ["estado", "fecha_prestamo", "vence"]
    search_fields = ["alumno_nombre", "alumno_dni", "ejemplar__titulo__titulo"]
    ordering = ["-fecha_prestamo"]
