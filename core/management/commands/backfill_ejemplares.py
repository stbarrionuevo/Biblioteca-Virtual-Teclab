from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Prestamo, Titulo, Ejemplar


class Command(BaseCommand):
    help = (
        "Vincula un Ejemplar a cada Prestamo que hoy tiene ejemplar = NULL.\n"
        "- Si el modelo viejo tenía Prestamo.libro como FK a Titulo → usa ese Titulo.\n"
        "- Si Prestamo.libro era un string (título) → busca Titulo por ese texto (case-insensitive).\n"
        "- Si no hay Ejemplar de ese Titulo, crea uno (PRESTADO si el préstamo no está devuelto; "
        "  DISPONIBLE si ya se devolvió)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula y no graba cambios (hace rollback automático).",
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        asignados = 0
        creados = 0
        sin_match = 0

        try:
            with transaction.atomic():
                qs = Prestamo.objects.filter(ejemplar__isnull=True)

                for p in qs:
                    t = None

                    # Caso 1: Prestamo.libro era FK a Titulo (si todavía existe ese campo)
                    if hasattr(p, "libro") and getattr(p, "libro", None) and hasattr(p.libro, "titulo"):
                        t = p.libro

                    # Caso 2: Prestamo.libro era texto (título)
                    elif hasattr(p, "libro") and isinstance(p.libro, str) and p.libro.strip():
                        t = Titulo.objects.filter(titulo__iexact=p.libro.strip()).first()

                    # Caso 3 (opcional): si el campo viejo se llamaba distinto
                    elif hasattr(p, "libro_titulo") and isinstance(p.libro_titulo, str) and p.libro_titulo.strip():
                        t = Titulo.objects.filter(titulo__iexact=p.libro_titulo.strip()).first()

                    if not t:
                        sin_match += 1
                        continue

                    ej = Ejemplar.objects.filter(titulo=t).first()
                    if not ej:
                        # Si el préstamo NO está devuelto → el ejemplar nace PRESTADO
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

                # En dry-run tiramos una excepción para forzar rollback del atomic,
                # pero igual mostramos los conteos.
                if dry:
                    self.stdout.write(self.style.WARNING("Dry-run: se simularon cambios, no se guardó nada."))
                    raise RuntimeError("Rollback (dry-run)")

        except RuntimeError as ex:
            if "dry-run" not in str(ex).lower():
                raise

        self.stdout.write(self.style.SUCCESS(
            f"Backfill finalizado → asignados: {asignados} · ejemplares creados: {creados} · sin match: {sin_match}"
        ))
