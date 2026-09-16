# SPECS — Proyecto Django "Biblioteca"

> Documento de especificaciones para que el agente implemente, configure y deje funcional el proyecto Django de biblioteca con CRUDs automáticos en el panel de administración, usando **MySQL** como motor de base de datos.

## Contexto general

- Nombre raíz del proyecto: **Biblioteca**
- Proyecto Django (carpeta interna del `startproject`): **BibliotecaProy**
- App Django (módulo): **catalogo**
- Motor de base de datos: **MySQL** (driver `mysqlclient`)
- Base de datos a crear: **biblioteca**
- El agente debe crear todo lo que falte del proyecto (estructura, entorno virtual, dependencias, modelos, admin, migraciones) y dejarlo corriendo con `manage.py runserver`.

Estructura de carpetas esperada al finalizar:

```text
Biblioteca/
├── entorno/                  # entorno virtual
└── BibliotecaProy/           # proyecto Django
    ├── manage.py
    ├── requirements.txt
    ├── BibliotecaProy/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── catalogo/
        ├── migrations/
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models.py
        ├── tests.py
        └── views.py
```

---

## Fase 0 — Preparación del entorno

### 0.1 Verificar/instalar Python
- Confirmar que Python 3.x está disponible (`python --version` o `py --version`).

### 0.2 Crear carpeta raíz y entorno virtual
- Crear carpeta raíz `Biblioteca/`.
- Dentro, crear entorno virtual `entorno`:
  ```bash
  python -m venv entorno
  ```
- Activarlo:
  - Windows: `entorno\Scripts\Activate`
  - Linux/Mac: `source entorno/bin/activate`

### 0.3 Instalar dependencias base
```bash
pip install django
pip install mysqlclient
```
- Si `mysqlclient` falla por falta de headers del sistema (común en Linux/Mac), documentar la alternativa `pip install pymysql` + shim de compatibilidad en `__init__.py` del proyecto, pero **la opción preferida es `mysqlclient`**.

**Criterio de aceptación:** `pip freeze` muestra `Django` y `mysqlclient` instalados dentro del entorno virtual.

---

## Fase 1 — Crear el proyecto Django

### 1.1 Generar el proyecto
Desde dentro de `Biblioteca/`:
```bash
django-admin startproject BibliotecaProy
```

### 1.2 Verificar arranque inicial
```bash
cd BibliotecaProy
python manage.py runserver
```
- Debe mostrar la pantalla de bienvenida de Django en `http://127.0.0.1:8000/`.
- Es normal que en este punto reporte migraciones pendientes (admin, auth, contenttypes, sessions); no aplicarlas todavía si ya se va a configurar MySQL primero.

**Criterio de aceptación:** el servidor arranca sin errores de importación/configuración.

---

## Fase 2 — Configurar MySQL como base de datos

### 2.1 Crear la base de datos en MySQL
- Nombre de la base de datos: `biblioteca`.
- El agente debe crearla vía cliente MySQL (o documentar el comando SQL si no tiene acceso directo):
  ```sql
  CREATE DATABASE biblioteca CHARACTER SET utf8mb4;
  ```

### 2.2 Configurar `settings.py`
Reemplazar el bloque `DATABASES` por:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'biblioteca',
        'USER': 'root',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

- Dejar comentado como referencia (no activo) el bloque equivalente de PostgreSQL:
```python
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'biblioteca',
#         'USER': 'postgres',
#         'PASSWORD': 'root',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
```
- Usuario/password de MySQL deben quedar como **variables configurables** (idealmente vía variables de entorno o un `.env`), no hardcodeadas en texto plano si el agente puede mejorar esto. Si no se implementa `.env`, al menos dejar un comentario indicando que deben ajustarse antes de producción.

**Criterio de aceptación:** Django puede conectar a MySQL sin errores.

---

## Fase 3 — Migraciones iniciales y superusuario

### 3.1 Migrar las apps base de Django
```bash
python manage.py makemigrations
python manage.py migrate
```
- Debe crear tablas: `auth_group`, `auth_group_permissions`, `auth_permission`, `auth_user`, `auth_user_groups`, `auth_user_user_permissions`, `django_admin_log`, `django_content_type`, `django_migrations`, `django_session`.

### 3.2 Crear superusuario
```bash
python manage.py createsuperuser
```
- Usar credenciales de prueba razonables (usuario, email, password). Si la contraseña es débil, el agente puede forzar la creación en modo desarrollo, pero debe advertir que no es apto para producción.

**Criterio de aceptación:** login exitoso en `http://127.0.0.1:8000/admin/` con el superusuario creado.

---

## Fase 4 — Crear la app `catalogo`

### 4.1 Generar la app
```bash
python manage.py startapp catalogo
```

### 4.2 Registrar la app en `settings.py`
Añadir a `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'catalogo.apps.CatalogoConfig',
]
```

- Verificar que `catalogo/apps.py` tenga:
```python
from django.apps import AppConfig

class CatalogoConfig(AppConfig):
    name = 'catalogo'
```

**Criterio de aceptación:** `python manage.py check` no reporta errores relacionados con la app `catalogo`.

---

## Fase 5 — Modelos (`catalogo/models.py`)

Implementar los 4 modelos siguientes, con **una modificación obligatoria** respecto al material original: el campo `language` de `Book` debe ser una lista desplegable (choices), no texto libre.

### 5.1 Imports necesarios al inicio del archivo
```python
from django.db import models
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
import uuid
from datetime import date
from django.conf import settings
```

### 5.2 Modelo `Genre`
```python
class Genre(models.Model):
    """Model representing a book genre (e.g. Science Fiction, Non Fiction)."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)"
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('genre-detail', args=[str(self.id)])

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='genre_name_case_insensitive_unique',
                violation_error_message="Genre already exists (case insensitive match)"
            ),
        ]
```

### 5.3 Modelo `Author`
```python
class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'
```

### 5.4 Modelo `Book` (con `language` como choices — REQUISITO NUEVO)

Opciones requeridas para el desplegable de idioma:
**Español, Lengua Indígena, Inglés, Francés**

```python
class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""

    LANGUAGE_CHOICES = (
        ('es', 'Español'),
        ('li', 'Lengua Indígena'),
        ('en', 'Inglés'),
        ('fr', 'Francés'),
    )

    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.RESTRICT, null=True)
    summary = models.TextField(
        max_length=1000, help_text="Enter a brief description of the book")
    isbn = models.CharField(
        'ISBN', max_length=13, unique=True,
        help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        blank=True,
        help_text="Select the book language"
    )

    class Meta:
        ordering = ['title', 'author']

    def display_genre(self):
        """Creates a string for the Genre. This is required to display genre in Admin."""
        return ', '.join([genre.name for genre in self.genre.all()[:3]])

    display_genre.short_description = 'Genre'

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    def __str__(self):
        return self.title
```

> Nota para el agente: `max_length=2` es suficiente para los códigos `es/li/en/fr`. Ajustar si se agregan más idiomas con códigos más largos.

### 5.5 Modelo `BookInstance`
```python
class BookInstance(models.Model):
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                           help_text="Unique ID for this particular book across whole library")
    book = models.ForeignKey('Book', on_delete=models.RESTRICT, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_overdue(self):
        return bool(self.due_back and date.today() > self.due_back)

    LOAN_STATUS = (
        ('d', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='d',
        help_text='Book availability')

    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)

    def get_absolute_url(self):
        return reverse('bookinstance-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.id} ({self.book.title})'
```

**Criterio de aceptación:** `python manage.py makemigrations catalogo` genera correctamente `0001_initial.py` con los 4 modelos y sin errores de referencias circulares.

---

## Fase 6 — Migrar el modelo de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

- Debe crear las tablas `catalogo_genre`, `catalogo_author`, `catalogo_book`, `catalogo_book_genre` (tabla intermedia M2M) y `catalogo_bookinstance`.

**Criterio de aceptación:** las tablas existen en la base de datos `biblioteca` (verificar con `SHOW TABLES;` en MySQL).

---

## Fase 7 — Registrar modelos en el panel de administración (`catalogo/admin.py`)

### 7.1 Import correcto
```python
from django.contrib import admin
from .models import Author, Book, BookInstance, Genre
```
> Importante: el import debe ser relativo (`.models`), **no** `BibliotecaProy.catalogo.models` (error típico del autocompletado).

### 7.2 Registro básico funcional (mínimo pedido en el material)
```python
admin.site.register(Genre)
```

### 7.3 Registro avanzado requerido (vista tabular de libros)

En vez de un `admin.site.register(Book)` simple, se requiere una vista en **lista tabular** que muestre columnas (no solo el título), tal como se pide explícitamente: título, autor y género.

```python
class BooksInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0


class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')
    inlines = [BooksInstanceInline]


admin.site.register(Book, BookAdmin)
```

### 7.4 Registro de `Author`
```python
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')


admin.site.register(Author, AuthorAdmin)
```

### 7.5 Registro de `BookInstance` (con filtros por estado, recomendado)
```python
@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'status', 'borrower', 'due_back', 'id')
    list_filter = ('status', 'due_back')

    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )
```

**Criterio de aceptación:**
- En `http://127.0.0.1:8000/admin/` aparece la sección **CATALOGO** con `Authors`, `Books`, `Book instances`, `Genres`.
- La lista de libros ("Select book to change") muestra columnas **TITLE / AUTHOR / GENRE**, no solo el título.
- Al crear/editar un libro, el campo `Language` aparece como lista desplegable con las 4 opciones pedidas (Español, Lengua Indígena, Inglés, Francés).

---

## Fase 8 — Carga de datos de prueba

- Crear al menos:
  - 2 autores
  - 3 géneros
  - 3 libros (cada uno con al menos 1 género, un idioma seleccionado del desplegable)
  - 2 instancias de libro (`BookInstance`) con distintos `status`
- Puede hacerse manualmente desde el admin o vía un script de `management command` / fixture si el agente prefiere automatizarlo (opcional, no bloqueante).

**Criterio de aceptación:** los datos son visibles y editables desde el panel de administración sin errores 500.

---

## Fase 9 — Extras de calidad de proyecto (recomendado, no bloqueante)

1. Generar `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```
2. Crear `.gitignore` (excluyendo `entorno/`, `__pycache__/`, `*.pyc`, `.env`, `db.sqlite3` si aplica).
3. Mover credenciales de MySQL a variables de entorno (`os.environ.get(...)`) si el agente tiene margen para hacerlo sin romper el flujo pedido.
4. Verificar `python manage.py check` sin warnings críticos antes de dar por cerrado el proyecto.

---

## Resumen de fases (checklist para el agente)

- [ ] Fase 0 — Entorno virtual y dependencias instaladas
- [ ] Fase 1 — Proyecto `BibliotecaProy` creado y arrancando
- [ ] Fase 2 — MySQL configurado en `settings.py` y BD `biblioteca` creada
- [ ] Fase 3 — Migraciones base aplicadas + superusuario creado
- [ ] Fase 4 — App `catalogo` creada y registrada en `INSTALLED_APPS`
- [ ] Fase 5 — Modelos `Genre`, `Author`, `Book` (con `language` como choices), `BookInstance` implementados
- [ ] Fase 6 — Migraciones de `catalogo` generadas y aplicadas
- [ ] Fase 7 — `admin.py` con registro avanzado (list_display tabular para Book, imports correctos)
- [ ] Fase 8 — Datos de prueba cargados
- [ ] Fase 9 — Extras de calidad (requirements.txt, .gitignore, credenciales)

**Definición de "hecho" para todo el proyecto:** `python manage.py runserver` corre sin errores, el admin en `/admin/` muestra la sección CATALOGO completa y funcional, el campo `Language` es un desplegable con las 4 opciones pedidas, y la lista de libros se ve en formato tabular con título/autor/género.
