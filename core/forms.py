from django import forms
from django.db import transaction
from datetime import date, timedelta
from .models import Titulo, Ejemplar, Prestamo, Categoria


class LibroForm(forms.ModelForm):
 
    categorias = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.order_by("nombre"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
        label="Categorías",
    )

    class Meta:
        model = Titulo
        fields = ["titulo", "autor", "categorias"]
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "required": True,
                "minlength": 2,
                "maxlength": 200,
                "placeholder": "Ej: Caso social individual",
            }),
            "autor": forms.TextInput(attrs={
                "class": "form-control",
                "required": True,
                "minlength": 2,
                "maxlength": 200,
                "placeholder": "Ej: Ricardo Hill",
            }),
        }
    @transaction.atomic
    def save(self, commit=True):
        titulo_obj = super().save(commit=commit)
        if not titulo_obj.ejemplares.exists():
            Ejemplar.objects.create(titulo=titulo_obj, estado="DISPONIBLE")
        return titulo_obj


class PrestamoForm(forms.ModelForm):
    """
    Crea un Prestamo y en save() marca el Ejemplar como PRESTADO.
    Valida fecha (rango 0–30 días, sin sábados ni domingos) y DNI.
    """
    fecha_devolucion = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Fecha de devolución",
    )

    class Meta:
        model = Prestamo

        fields = ["alumno_nombre", "alumno_dni", "ejemplar"]
        widgets = {
            "alumno_nombre": forms.TextInput(attrs={"class": "form-control", "maxlength": 200}),
            "alumno_dni":   forms.TextInput(attrs={"class": "form-control", "maxlength": "8", "inputmode": "numeric"}),
            "ejemplar":     forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "alumno_nombre": "Alumno",
            "alumno_dni": "DNI",
            "ejemplar": "Ejemplar (libro)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["ejemplar"].queryset = (
            Ejemplar.objects.filter(estado="DISPONIBLE")
            .select_related("titulo")
            .order_by("titulo__titulo")
        )
        self.fields["ejemplar"].label_from_instance = (
            lambda obj: f"{obj.titulo.titulo} · Ejemplar #{obj.pk}"
        )


    def clean_fecha_devolucion(self):
        f = self.cleaned_data["fecha_devolucion"]
        hoy = date.today()
        max_date = hoy + timedelta(days=30)
        if not (hoy <= f <= max_date):
            raise forms.ValidationError("La fecha debe estar entre hoy y 30 días.")
        if f.weekday() in (5, 6): 
            raise forms.ValidationError("La fecha no puede caer sábado ni domingo.")
        return f

    def clean_alumno_dni(self):
        dni = (self.cleaned_data.get("alumno_dni") or "").strip()
        if not dni.isdigit() or not (7 <= len(dni) <= 8):
            raise forms.ValidationError("DNI inválido (solo números, 7–8 dígitos).")
        return dni

    def clean_ejemplar(self):
        ej = self.cleaned_data["ejemplar"]
        if ej.estado != "DISPONIBLE":
            raise forms.ValidationError("El ejemplar seleccionado no está disponible.")
        return ej

    @transaction.atomic
    def save(self, commit=True):
        """
        - Setea fecha_prestamo (hoy) y estado=ACTIVO
        - Setea vence = fecha_devolucion (del form)
        - Marca el Ejemplar como PRESTADO
        """
        obj = super().save(commit=False)
        if not obj.fecha_prestamo:
            obj.fecha_prestamo = date.today()
        obj.estado = "ACTIVO"
        obj.vence = self.cleaned_data["fecha_devolucion"]

        if commit:
            obj.save()
            ej = obj.ejemplar
            if ej.estado != "PRESTADO":
                ej.estado = "PRESTADO"
                ej.save(update_fields=["estado"])
        return obj
