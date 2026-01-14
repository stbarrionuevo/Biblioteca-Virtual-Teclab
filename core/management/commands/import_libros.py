from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Titulo, Ejemplar, Categoria

from pathlib import Path
import csv

# ---------- Config flexible de columnas ----------
ALIASES = {
    # claves estándar : posibles encabezados (normalizados)
    "titulo": [
        "nombre del libro", "titulo", "título", "nombre", "nombre del material",
        "título del libro", "titulo del libro", "libro", "obra", "titulo/obra"
    ],
    "autor": ["autor", "autores"],
    "categoria": ["tematica", "temática", "tema", "materia", "categoría", "categoria"],
    "stock": ["stock", "cantidad", "ejemplares", "n° ejemplares"],
}

# ---------- Categorización ----------
CANONICAL_CATEGORIES = [
    "Psicología",
    "Social",
    "Adolescencia/Niñez",
    "Teología",
    "Ética",
    "Naturaleza",
    "Informática",
    "Género",
    "Adicciones",
    "Trabajo",
    "Técnicas y Metodologías",
    "Investigación/Análisis",
]

KEYWORD_RULES = [
    (["social", "vida", "grupo", "sociales", "sociologia", "sociología", "comunidad", "individuo", "equipo", "familiar", "modelos", "edi"], "Social"),
    (["psicologia", "salud mental", "psicología", "clinica", "clínica", "terapia", "emocional"], "Psicología"),
    (["adolescencia", "adolescente", "juvenil", "infantil", "adopcion", "niñez", "ninez", "niños", "ninos"], "Adolescencia/Niñez"),
    (["género", "genero", "mujeres", "esi", "femeninas"], "Género"),
    (["teologia", "teología"], "Teología"),
    (["ética", "etica"], "Ética"),
    (["naturaleza"], "Naturaleza"),
    (["informatica", "informática"], "Informática"),
    (["drogas", "consumo"], "Adicciones"),
    (["laboral", "práctica", "practica", "trabajo"], "Trabajo"),
    (["metodologico", "metodologica", "tecnica", "técnica", "tecnicas", "metodos", "metodologicos", "elementos"], "Técnicas y Metodologías"),
    (["investigacion", "análisis", "analisis", "teorias", "teorías"], "Investigación/Análisis"),
]

FALLBACK_CATEGORY = "Otros"


# ---------- Utils ----------
def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    for a, b in (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
        ("ä", "a"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u"),
        ("ñ", "n"),
    ):
        s = s.replace(a, b)
    return " ".join(s.split())


def norm_str(x):
    return (str(x).strip() if x is not None else "")


def map_headers(fieldnames):
    """
    Devuelve dict con la columna original para cada clave estándar de ALIASES.
    """
    headers_norm = {orig: _norm_text(orig) for orig in (fieldnames or [])}
    mapped = {k: None for k in ALIASES.keys()}
    for key, alias_list in ALIASES.items():
        alias_set = set(_norm_text(a) for a in alias_list)
        for orig, normed in headers_norm.items():
            if normed in alias_set:
                mapped[key] = orig
                break
    return mapped


def categoria_por_keywords(*textos: str) -> str | None:
    """
    Recorre KEYWORD_RULES en orden y devuelve la primera categoría canónica que matchee.
    """
    hay = _norm_text(" ".join([t for t in textos if t]))
    if not hay:
        return None
    for keywords, cat in KEYWORD_RULES:
        for kw in keywords:
            if _norm_text(kw) in hay:
                return cat
    return None


def parse_stock(value) -> int:
    """
    Convierte el campo stock a entero >= 1. Si no viene o no es válido, usa 1.
    """
    s = norm_str(value)
    if not s:
        return 1
    try:
        n = int(float(s.replace(",", ".").strip()))
        return max(1, n)
    except Exception:
        return 1


# ---------- Comando principal ----------
class Command(BaseCommand):
    help = "Importa títulos desde CSV (sin pandas). Mapea columnas flexible, asigna categorías y crea ejemplares (stock)."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Ruta al .csv (UTF-8).")
        parser.add_argument("--limpiar", action="store_true", help="Borra TODOS los títulos/ejemplares antes de importar.")
        parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en DB.")
        parser.add_argument("--delimiter", type=str, default=None, help="Delimitador (auto si no se indica).")
        parser.add_argument("--header-row", type=int, default=1, help="Número de fila donde está la cabecera (1 = primera).")
        parser.add_argument("--debug", action="store_true", help="Muestra encabezados detectados y mapeo.")
        # Overrides manuales
        parser.add_argument("--col-titulo", type=str, default=None)
        parser.add_argument("--col-autor", type=str, default=None)
        parser.add_argument("--col-categoria", type=str, default=None)
        parser.add_argument("--col-stock", type=str, default=None)

    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            self.stdout.write(self.style.ERROR(f"No existe el archivo: {path}"))
            return

        # --- Sniff delimiter sobre sample de texto ---
        delimiter = opts["delimiter"]
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                sample = f.read(4096)
                if delimiter is None:
                    try:
                        sniffer = csv.Sniffer()
                        dialect = sniffer.sniff(sample, delimiters=[",", ";", "|", "\t"])
                        delimiter = dialect.delimiter
                    except Exception:
                        delimiter = ","
        except UnicodeDecodeError:
            self.stdout.write(self.style.ERROR("El CSV debe estar en UTF-8. Al guardar desde Excel elegí 'CSV UTF-8'."))
            return

        # --- Abrimos y saltamos filas hasta la cabecera real, luego DictReader ---
        with open(path, "r", encoding="utf-8", newline="") as f:
            header_row = int(opts.get("header_row") or 1)
            for _ in range(max(0, header_row - 1)):
                next(f, None)

            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames:
                self.stdout.write(self.style.ERROR("No se encontraron encabezados en el CSV."))
                return

            if opts["debug"]:
                self.stdout.write("Encabezados originales (fila detectada):")
                for h in reader.fieldnames:
                    self.stdout.write(f"  - {h!r}")

            mapping = map_headers(reader.fieldnames)

            # Permitir overrides manuales desde CLI
            col_titulo = opts["col_titulo"] or mapping.get("titulo")
            col_autor = opts["col_autor"] or mapping.get("autor")
            col_cat = opts["col_categoria"] or mapping.get("categoria")
            col_stock = opts["col_stock"] or mapping.get("stock")

            if opts["debug"]:
                self.stdout.write("Normalizados y mapeados:")
                self.stdout.write(f"{'titulo':>12}: {col_titulo!r}")
                self.stdout.write(f"{'autor':>12}: {col_autor!r}")
                self.stdout.write(f"{'categoria':>12}: {col_cat!r}")
                self.stdout.write(f"{'stock':>12}: {col_stock!r}")
                self.stdout.write(
                    f"Usando columnas -> titulo={col_titulo!r}, autor={col_autor!r}, categoria={col_cat!r}, stock={col_stock!r}"
                )

            if not col_titulo:
                self.stdout.write(self.style.ERROR("No encontré la columna de TÍTULO (ej: 'NOMBRE DEL LIBRO', 'TÍTULO')."))
                return

            # --- Confirmación de borrado si corresponde ---
            if opts["limpiar"] and not opts["dry_run"]:
                with transaction.atomic():
                    Ejemplar.objects.all().delete()
                    Titulo.objects.all().delete()
                self.stdout.write(self.style.WARNING("Se borraron TODOS los títulos y ejemplares (limpieza previa)."))

            creados_t = actualizados_t = nuevos_ej = 0
            filas_sin_titulo = 0

            # --- Proceso principal ---
            with transaction.atomic():
                for row in reader:
                    titulo_txt = norm_str(row.get(col_titulo)) if col_titulo else ""
                    if not titulo_txt:
                        filas_sin_titulo += 1
                        continue

                    autor_txt = norm_str(row.get(col_autor)) if col_autor else ""
                    categoria_raw = norm_str(row.get(col_cat)) if col_cat else ""
                    stock_n = parse_stock(row.get(col_stock)) if col_stock else 1

                    # Categoría por keywords si no hay o para normalizar
                    cat_final = categoria_por_keywords(categoria_raw, titulo_txt) or FALLBACK_CATEGORY
                    if cat_final not in CANONICAL_CATEGORIES and cat_final != FALLBACK_CATEGORY:
                        cat_final = FALLBACK_CATEGORY

                    if opts["dry_run"]:
                        # Simulación de creación/actualización
                        if Titulo.objects.filter(titulo=titulo_txt).exists():
                            actualizados_t += 1
                        else:
                            creados_t += 1
                            nuevos_ej += max(1, stock_n)
                        continue

                    # ----- Escritura real -----
                    titulo_obj, created = Titulo.objects.get_or_create(
                        titulo=titulo_txt,
                        defaults={"autor": autor_txt}
                    )
                    if not created:
                        # actualizar autor si vino y cambió
                        if autor_txt and autor_txt != titulo_obj.autor:
                            titulo_obj.autor = autor_txt
                            titulo_obj.save(update_fields=["autor"])
                        actualizados_t += 1
                    else:
                        creados_t += 1

                    # Categorías: asegurar cat_final
                    cat_objs = []
                    for c in [cat_final]:
                        cat_obj, _ = Categoria.objects.get_or_create(nombre=c)
                        cat_objs.append(cat_obj)
                    # set/add sin perder otras si ya tiene
                    for c in cat_objs:
                        titulo_obj.categorias.add(c)

                    # Stock / ejemplares
                    existentes = titulo_obj.ejemplares.count()
                    a_crear = max(0, stock_n - existentes)
                    if a_crear > 0:
                        to_create = [Ejemplar(titulo=titulo_obj, estado="DISPONIBLE") for _ in range(a_crear)]
                        Ejemplar.objects.bulk_create(to_create)
                        nuevos_ej += a_crear

            pref = "[DRY-RUN] " if opts["dry_run"] else ""
            self.stdout.write(self.style.SUCCESS(
                f"{pref}Import listo → Títulos creados: {creados_t} · Títulos actualizados: {actualizados_t} · "
                f"Ejemplares nuevos: {nuevos_ej} · Filas sin título: {filas_sin_titulo}"
            ))
