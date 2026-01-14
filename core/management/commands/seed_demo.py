from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Libro, Prestamo
import random
from datetime import date, timedelta

CATEGORIAS = [
    "Ciencia", "Psicología", "Social", "Historia", "Literatura",
    "Filosofía", "Infantil", "Matemática", "Tecnología", "Arte"
]

AUTORES = [
    "Gabriel García Márquez", "Stephen King", "Carl Sagan", "Jane Austen",
    "George Orwell", "Isabel Allende", "Jorge Luis Borges", "Haruki Murakami",
    "Ursula K. Le Guin", "Hannah Arendt", "Mario Vargas Llosa", "Umberto Eco",
]

ALUMNOS = [
    "Juan Pérez", "Lucía Fernández", "Diego Martínez", "Ana García",
    "Sofía López", "Marcos Ortega", "Valentina Díaz", "Nicolás Ríos",
    "Micaela Cortina", "Pilar Romero", "Tomás Castro", "Agustina Reyes",
]

def gen_titulo(i):
    base = ["El secreto de", "Introducción a", "Manual de", "Teoría de",
            "Breve historia de", "Fundamentos de", "El arte de", "La esencia de"]
    tema = ["la mente", "las palabras", "la física", "la sociedad",
            "la educación", "los algoritmos", "la historia", "la lectura"]
    return f"{random.choice(base)} {random.choice(tema)} #{i}"

class Command(BaseCommand):
    help = "Crea N libros de demo y (opcional) M préstamos repartidos (algunos atrasados, otros próximos)."

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=40, help="Cantidad de libros a crear (default: 40)")
        parser.add_argument("--prestamos", type=int, default=15, help="Cantidad de préstamos de demo a crear (default: 15)")
        parser.add_argument("--limpiar", action="store_true",
                            help="Borra Libros y Prestamos antes de sembrar (cuidado: elimina datos).")

    @transaction.atomic
    def handle(self, *args, **opts):
        n = opts["n"]
        m = opts["prestamos"]
        limpiar = opts["limpiar"]

        if limpiar:
            Prestamo.objects.all().delete()
            Libro.objects.all().delete()
            self.stdout.write(self.style.WARNING("Se limpiaron Libros y Prestamos."))

     
        creados = 0
        for i in range(1, n + 1):
            titulo = gen_titulo(i)
            autor = random.choice(AUTORES)
            categoria = random.choice(CATEGORIAS)
            estado = "Disponible"  

            obj, ok = Libro.objects.get_or_create(
                titulo=titulo,
                defaults={"autor": autor, "categoria": categoria, "estado": estado}
            )
            if ok:
                creados += 1

        self.stdout.write(self.style.SUCCESS(f"Libros creados: {creados} (de {n} pedidos)."))

 
        libros_disponibles = list(Libro.objects.filter(estado="Disponible"))
        random.shuffle(libros_disponibles)
        m = min(m, len(libros_disponibles))  
        hoy = date.today()

        creados_p = 0
        for i in range(m):
            libro = libros_disponibles[i]
            alumno = random.choice(ALUMNOS)
            dni = str(random.randint(30000000, 50000000))

      
            delta_vence = random.randint(-5, 10)
            vence = hoy + timedelta(days=delta_vence)

        
            p = Prestamo.objects.create(
                alumno=alumno,
                dni=dni,
                libro=libro,
                vence=vence,
                devuelto=False
            )
   
            try:
                days_back = random.randint(0, 14)
                fecha_p = hoy - timedelta(days=days_back)
                Prestamo.objects.filter(pk=p.pk).update(fecha_prestamo=fecha_p)
            except Exception:
                pass 

          
            libro.estado = "Prestado"
            libro.save(update_fields=["estado"])
            creados_p += 1

        self.stdout.write(self.style.SUCCESS(f"Préstamos creados: {creados_p} (activos)."))
        self.stdout.write(self.style.SUCCESS("Seed de demo completo."))
