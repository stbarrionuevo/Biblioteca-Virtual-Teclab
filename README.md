# 📚 Sistema de Biblioteca – Escuela Diocesana (Prototipo v0.3)

Aplicación web en **Django 5.2.5** para gestionar el catálogo de libros y préstamos de la biblioteca escolar.  
Incluye: alta de títulos con múltiples categorías, creación/eliminación de categorías (AJAX), stock por ejemplar, préstamos con renovar/devolver/eliminar, listados con filtros y **exportación a Excel/CSV**.

> **Estado**: Prototipo funcional. Falta aplicar **logo y paleta institucional** (listo para integrar).

---

## ✨ Funcionalidades

- **Libros**
  - Alta de títulos (título, autor) con **múltiples categorías**.
  - Si no se elige categoría → se asigna **“Otros”** por defecto.
  - Se crea **1 ejemplar DISPONIBLE** automáticamente al guardar.
  - Listado con **filtros** (búsqueda y categoría), **paginación** y **conteo de stock**:
    - `Disponible` = ejemplares con estado `DISPONIBLE`
    - `Prestado` = ejemplares con estado `PRESTADO`
  - **Exportar** resultados (con filtros aplicados) a **Excel (.xlsx)** o **CSV (.csv)**.

- **Categorías**
  - **Crear** nueva categoría por **AJAX** (queda seleccionada al instante).
  - **Eliminar** categoría reasignando títulos a **“Otros”** si quedaran sin categorías.

- **Préstamos**
  - Alta de préstamo: valida **DNI** (7–8 dígitos), fecha (0–30 días, **sin sábados/ domingos**), y **disponibilidad** del ejemplar.
  - Acciones por préstamo:
    - **Renovar** (+7 días, estado `RENOVADO`)
    - **Devolver** (marca préstamo `DEVUELTO` y el ejemplar `DISPONIBLE`)
    - **Eliminar** (si no estaba devuelto, libera stock antes)
  - Badges de estado:
    - `ACTIVO` (azul)
    - `RENOVADO` (amarillo)
    - `DEVUELTO` (gris)
    - **`VENCIDO` (rojo)** si la fecha venció y no se devolvió

- **Dashboard**
  - Totales: stock, prestados, disponibles y % de ocupación.
  - Listas de **vence en 7 días** y **atrasados**.

---

## 🧰 Stack

- **Backend**: Python 3.11, Django 5.2.5
- **DB**: SQLite (desarrollo)
- **Frontend**: Plantillas Django + Bootstrap 5
- **Export**: `openpyxl` (Excel) / `csv` nativo

---

## 📁 Estructura (simplificada)

biblioteca/
├─ core/
│ ├─ migrations/
│ ├─ static/
│ │ ├─ css/theme.css
│ │ └─ img/{logo.png, favicon.ico}
│ ├─ templates/
│ │ ├─ base.html
│ │ ├─ dashboard.html
│ │ ├─ libros_list.html
│ │ ├─ libro_form.html
│ │ ├─ prestamo_form.html
│ │ └─ prestamos_list.html
│ ├─ admin.py
│ ├─ forms.py
│ ├─ models.py
│ ├─ views.py
│ └─ management/commands/
│ └─ import_libros.py
├─ biblioteca/
│ ├─ settings.py
│ ├─ urls.py
│ └─ wsgi.py
├─ db.sqlite3
├─ manage.py
└─ README.md

yaml
Copiar código

---

## 🚀 Puesta en marcha

### Requisitos
- Python **3.11**
- `pip` y `venv`

### Instalación (Windows)
```bash
# 1) Clonar repo
git clone https://github.com/tu-usuario/biblioteca.git
cd biblioteca

# 2) Crear y activar venv
python -m venv venv
venv\Scripts\activate

# 3) Instalar dependencias
pip install -r requirements.txt

# pip install django==5.2.5 openpyxl
Migraciones y superusuario
bash
Copiar código
python manage.py migrate
python manage.py createsuperuser
Correr el servidor
bash
Copiar código
python manage.py runserver
# http://127.0.0.1:8000


📦 Importar catálogo (CSV)
El proyecto incluye un comando import_libros que intenta detectar encabezados, normalizar y crear títulos/ejemplares.
Soporta cabeceras como: NOMBRE DEL LIBRO / TÍTULO, AUTOR, TEMÁTICA / CATEGORÍA.

bash
Copiar código
# Vista previa (no escribe en DB)
python manage.py import_libros "C:\ruta\archivo.csv" --dry-run --debug

# Si tu CSV usa otro delimitador:
python manage.py import_libros "C:\ruta\archivo.csv" --delimiter ";" --dry-run

# Si las cabeceras no están en la primera fila:
python manage.py import_libros "C:\ruta\archivo.csv" --header-row 3 --dry-run


python manage.py import_libros "C:\ruta\archivo.csv" --delimiter ";" --header-row 3
Tip: El campo stock es opcional. Por defecto se crea 1 ejemplar por título al importar.

📑 Exportar catálogo (Excel/CSV)
En el listado Libros hay botones de Descargar Excel y Descargar CSV.
Respetan filtros (búsqueda/categoría) y exportan las columnas:

Título · Autor · Categorías · Disponibles · Prestados

🧩 Modelos (resumen)
Categoria: nombre (único). Existe garantizada la categoría “Otros”.

Titulo: titulo, autor, categorias (M2M).

Ejemplar: titulo (FK), estado ∈ {DISPONIBLE, PRESTADO}.

Prestamo: ejemplar (FK), alumno_nombre, alumno_dni, fecha_prestamo, vence, estado ∈ {ACTIVO, RENOVADO, DEVUELTO}.

🖥️ Vistas principales
Dashboard: /

Libros

Listar: /libros/

Nuevo: /libros/nuevo/

Export: /libros/export/?format=xlsx|csv

Préstamos

Listar: /prestamos/

Nuevo: /prestamos/nuevo/

Renovar: /prestamos/<id>/renovar/ (POST)

Devolver:/prestamos/<id>/devolver/ (POST)

Eliminar:/prestamos/<id>/eliminar/ (POST)

## 📸 Capturas del sistema

### Dashboard
![Dashboard](screenshots/layout-biblioteca.png)

### Gestión de libros
![Libros](screenshots/libros.png)

### Préstamos
![Préstamos](screenshots/prestamos.png)

### Carga de libro
![Cargar libro](screenshots/cargar-libro.png)


Categorías

Crear (AJAX): /categorias/create/ (POST, JSON)

Eliminar: /categorias/<id>/delete/ (POST)

🧪 Validaciones clave
DNI: solo números (7–8 dígitos).

Fecha de devolución: rango 0–30 días, sin sábados ni domingos.

Ejemplar: debe estar DISPONIBLE para prestarse.

Préstamo vencido: si la fecha venció y no se devolvió, se muestra Vencido (rojo).


🙌 Agradecimientos
Docentes y directivos de la Escuela Diocesana.