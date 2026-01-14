from django.db import models
from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class Titulo(models.Model):
    TIPO_CHOICES = [
        ("LIBRO", "Libro"),
        ("TRABAJO", "Trabajo/Informe/Tesis/Monografía"),
    ]
    titulo      = models.CharField(max_length=200, unique=True)
    autor       = models.CharField(max_length=200, blank=True)
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES, default="LIBRO")


    lugar_edicion = models.CharField(max_length=120, blank=True)
    editorial     = models.CharField(max_length=120, blank=True)
    anio          = models.CharField(max_length=10, blank=True)
    edicion       = models.CharField(max_length=50, blank=True)
    isbn          = models.CharField(max_length=32, blank=True)


    categorias = models.ManyToManyField(Categoria, blank=True, related_name="titulos")

    class Meta:
        ordering = ["titulo"]

    def __str__(self):
            return self.titulo
        
def ensure_categoria_otros():
    return Categoria.objects.get_or_create(nombre="Otros")[0]


@receiver(post_migrate)
def create_otros_after_migrate(sender, **kwargs):
        
        try:
            ensure_categoria_otros()
        except Exception:
            pass

class Ejemplar(models.Model):
    ESTADO_CHOICES = [
        ("DISPONIBLE", "Disponible"),
        ("PRESTADO", "Prestado"),
    ]
    titulo = models.ForeignKey(Titulo, on_delete=models.CASCADE, related_name="ejemplares")
    codigo = models.CharField(max_length=50, blank=True) 
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="DISPONIBLE")

    class Meta:
        ordering = ["titulo_id", "id"]

    def __str__(self):
        return f"{self.titulo.titulo} — Ejemplar #{self.id or '—'}"

class Prestamo(models.Model):
    ESTADO_PRESTAMO = [
        ("ACTIVO", "Activo"),
        ("RENOVADO", "Renovado"),
        ("VENCIDO", "Vencido"),
        ("DEVUELTO", "Devuelto"),
    ]
    ejemplar = models.ForeignKey(
        'Ejemplar',
        null=True, blank=True,                   # ← permitir null temporalmente
        on_delete=models.PROTECT,
        related_name='prestamos'
    )
    alumno_nombre  = models.CharField(max_length=200)
    alumno_dni     = models.CharField(max_length=8, blank=True, null=True)
    fecha_prestamo = models.DateField(default=timezone.now)
    vence          = models.DateField()
    estado         = models.CharField(max_length=10, choices=ESTADO_PRESTAMO, default="ACTIVO")

    class Meta:
        ordering = ["-fecha_prestamo"]

    def __str__(self):
        return f"{self.ejemplar} → {self.alumno_nombre}"

   
    def renovar_7(self):
        from datetime import timedelta
        self.vence = self.vence + timedelta(days=7)
        self.estado = "RENOVADO"
        self.save()

    def marcar_devuelto(self):
        self.estado = "DEVUELTO"
        self.save()
        e = self.ejemplar
        e.estado = "DISPONIBLE"
        e.save()
