from django.db import transaction
from core.models import Prestamo, Titulo, Ejemplar

def backfill_ejemplares_en_prestamos():
    """
    Vincula un Ejemplar a cada Prestamo que hoy tiene ejemplar = NULL.
    - Si el modelo viejo tenía Prestamo.libro como FK a Titulo → usa ese Titulo.
    - Si Prestamo.libro era un string (título) → busca Titulo por ese texto (case-insensitive).
    - Si no hay Ejemplar de ese Titulo, crea uno (PRESTADO si el préstamo no está devuelto; DISPONIBLE si ya se devolvió).
    Devuelve (asignados, creados, sin_match).
    """
    asignados = 0
    creados = 0
    sin_match = 0

    with transaction.atomic():
        qs = Prestamo.objects.filter(ejemplar__isnull=True)
        for p in qs:
            t = None

     
            if hasattr(p, "libro") and getattr(p, "libro", None) and hasattr(p.libro, "titulo"):
                t = p.libro

      
            elif hasattr(p, "libro") and isinstance(p.libro, str) and p.libro.strip():
                t = Titulo.objects.filter(titulo__iexact=p.libro.strip()).first()

      
            elif hasattr(p, "libro_titulo") and isinstance(p.libro_titulo, str) and p.libro_titulo.strip():
                t = Titulo.objects.filter(titulo__iexact=p.libro_titulo.strip()).first()

            if not t:
                sin_match += 1
                continue

            ej = Ejemplar.objects.filter(titulo=t).first()
            if not ej:
            
                esta_devuelto = False
                if hasattr(p, "estado"):
                    esta_devuelto = (str(p.estado).upper() == "DEVUELTO")
                elif hasattr(p, "devuelto"):
                    esta_devuelto = bool(p.devuelto)

                estado_ej = "DISPONIBLE" if esta_devuelto else "PRESTADO"
                ej = Ejemplar.objects.create(titulo=t, estado=estado_ej)
                creados += 1

            p.ejemplar = ej
            p.save(update_fields=["ejemplar"])
            asignados += 1

    return asignados, creados, sin_match
if __name__ == "__main__":
    print(backfill_ejemplares_en_prestamos())