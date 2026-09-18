# SPECS v2 — Proyecto Django "Biblioteca"
## Módulo de Autores: modelo, vistas, plantillas y navegación

> **Versión:** 2.0
> **Base:** SPECS v1 ya implementadas (proyecto `BibliotecaProy`, app `catalogo`, MySQL, admin con CRUDs, `pagina_maestra.html` con Bootstrap 5, vistas `home`, lista de libros y detalle de libro ya funcionando).
> **Objetivo de esta versión:** completar el módulo de Autores (modelo ampliado, vista lista, vista detalle, plantillas y enlace en el menú), sin romper nada de lo ya existente.

---

## ⚠️ Reglas de alcance (leer antes de tocar código)

El agente **NO debe**:

- Modificar los modelos `Genre`, `Book` ni `BookInstance`.
- Cambiar la configuración de base de datos, `INSTALLED_APPS` ni `settings.py` (salvo que falte `TEMPLATES['DIRS']`, ver Fase 3.0).
- Reescribir `pagina_maestra.html`, `home`, `book_list.html` ni `book_detail.html`. Solo se toca **una línea** de `pagina_maestra.html` (el `href` de "Lista de autores") y, si aplica, el contexto del `home` para el contador de autores.
- Borrar o regenerar migraciones anteriores (`0001_initial.py`, etc.). Las nuevas migraciones son **incrementales**.
- Cambiar el estilo/estética ya definido; las plantillas nuevas deben reutilizar las clases Bootstrap 5 ya usadas en las plantillas de libros.

El agente **SÍ debe** seguir la misma convención y estructura que ya se usó para libros (mismo patrón de vistas, mismo naming de plantillas, mismo estilo de URLs).

---

## Estado esperado al finalizar

```text
BibliotecaProy/
├── BibliotecaProy/
│   ├── settings.py
│   └── urls.py
└── catalogo/
    ├── migrations/
    │   ├── 0001_initial.py            (existente — NO tocar)
    │   └── 000X_author_pen_name_...   (NUEVA)
    ├── models.py                      (Author modificado)
    ├── views.py                       (+ AuthorListView, AuthorDetailView)
    ├── urls.py                        (+ rutas 'authors' y 'author-detail')
    └── templates/
        └── catalogo/
            ├── pagina_maestra.html    (1 línea modificada)
            ├── book_list.html         (existente — NO tocar)
            ├── book_detail.html       (existente — NO tocar)
            ├── author_list.html       (NUEVA)
            └── author_detail.html     (NUEVA)
```

> Si en el proyecto actual las plantillas viven en otra ruta (`templates/` a nivel de proyecto, o sin la subcarpeta `catalogo/`), **respetar la ruta existente** y colocar las nuevas plantillas junto a las de libros.

---

# FASE 1 — Modificación del modelo `Author`

## Tarea 1.1 — Ajustar longitudes de campos existentes

En `catalogo/models.py`, dentro de la clase `Author`:

- `first_name`: cambiar `max_length=100` → `max_length=40`
- `last_name`: cambiar `max_length=100` → `max_length=40`

> No tocar `date_of_birth`, `date_of_death`, el `Meta.ordering`, `get_absolute_url()` ni `__str__()`.

## Tarea 1.2 — Agregar campo `pen_name` (seudónimo, opcional)

```python
pen_name = models.CharField(max_length=60, null=True, blank=True)
```

- Es **opcional**: acepta nulos en BD (`null=True`) y vacío en formularios (`blank=True`).
- No requiere valor por defecto en la migración.

## Tarea 1.3 — Agregar campo `nationality` (nacionalidad, obligatoria)

```python
nationality = models.CharField(max_length=40)
```

- **Sin** `null=True` y **sin** `blank=True`. Es un campo obligatorio.
- Esto es lo que provocará el prompt de migración de la Fase 2.

## Tarea 1.4 — Resultado esperado del modelo

```python
class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    pen_name = models.CharField(max_length=60, null=True, blank=True)
    nationality = models.CharField(max_length=40)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'
```

**Criterio de aceptación Fase 1:** `python manage.py check` sin errores y el modelo contiene los 6 campos con los `max_length` indicados.

---

# FASE 2 — Migración de la base de datos (desafío técnico)

## Contexto del problema

La tabla `catalogo_author` **ya tiene registros**. Al agregar `nationality` como campo obligatorio (NOT NULL, sin default), Django no sabe qué valor poner en las filas existentes, por lo que al ejecutar `makemigrations` mostrará:

```
You are trying to add a non-nullable field 'nationality' to author without a default;
we can't do that (the database needs something to populate existing rows).
Please select a fix:
 1) Provide a one-off default now
 2) Quit, and let me add a default in models.py
```

## Tarea 2.1 — Resolver el prompt de `nationality`

Elegir **una** de las dos rutas y documentarla (se pide evidencia en la Fase 6):

### Opción A (recomendada para la evidencia) — Valor único ahora
1. Ejecutar `python manage.py makemigrations`
2. Seleccionar la opción `1`
3. Escribir el valor entre comillas, por ejemplo: `'Desconocida'` (o `'Mexicana'`)
4. Django rellenará ese valor en todas las filas existentes y dejará el campo NOT NULL sin default permanente

### Opción B — Default en `models.py`
1. Seleccionar la opción `2` para salir
2. Agregar temporalmente `default='Desconocida'` al campo en `models.py`
3. Ejecutar `makemigrations` y `migrate`
4. (Opcional) Quitar el `default` después y generar una segunda migración

> **No** usar `null=True` para esquivar el problema: el requisito explícito es que `nationality` sea obligatorio.

## Tarea 2.2 — Verificar la longitud de los datos existentes

Antes de migrar, comprobar que ningún `first_name` o `last_name` existente exceda 40 caracteres, ya que MySQL puede truncar o fallar al reducir el `max_length`:

```sql
SELECT id, first_name, last_name FROM catalogo_author
WHERE CHAR_LENGTH(first_name) > 40 OR CHAR_LENGTH(last_name) > 40;
```

Si hay registros afectados, corregirlos manualmente antes de migrar.

## Tarea 2.3 — Aplicar la migración

```bash
python manage.py makemigrations
python manage.py migrate
```

**Criterio de aceptación Fase 2:**
- Se genera una migración nueva en `catalogo/migrations/` (no se modifica `0001_initial.py`).
- `migrate` aplica sin errores.
- En MySQL, `DESCRIBE catalogo_author;` muestra `pen_name` (NULL permitido) y `nationality` (NOT NULL), y `first_name`/`last_name` como `varchar(40)`.
- Los autores previamente registrados conservan sus datos y tienen el valor por defecto en `nationality`.

---

# FASE 3 — Vistas de Autores (`catalogo/views.py`)

## Tarea 3.0 — Verificación previa

Confirmar que `settings.py` ya tiene configurado el `TEMPLATES['DIRS']` / `APP_DIRS` que usan las plantillas de libros. **Si ya funciona para libros, no tocar nada.**

Confirmar también qué patrón se usó para libros (vistas basadas en clases `ListView`/`DetailView` o funciones) y **replicar el mismo patrón**.

## Tarea 3.1 — Import del modelo

Asegurar que `views.py` importe `Author`:

```python
from django.views import generic
from .models import Author
```

## Tarea 3.2 — Vista de lista de autores

```python
class AuthorListView(generic.ListView):
    model = Author
    template_name = 'catalogo/author_list.html'
    context_object_name = 'author_list'
    paginate_by = 10
```

- `paginate_by` es opcional; incluirlo solo si la lista de libros ya usa paginación, para mantener consistencia.

## Tarea 3.3 — Vista de detalle de autor

```python
class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalogo/author_detail.html'
    context_object_name = 'author'
```

- Busca por `pk` automáticamente. Devuelve 404 si el autor no existe.

## Tarea 3.4 — Contador de autores en el Home

Verificar la vista `home`. Si ya cuenta libros pero **no** autores, agregar al contexto:

```python
num_authors = Author.objects.count()
```

y exponerlo en la plantilla del home con la misma estructura de tarjeta (card) que ya usan los demás contadores. **No rediseñar el home**, solo agregar/actualizar la tarjeta del contador de autores.

**Criterio de aceptación Fase 3:** las vistas existen, importan `Author` correctamente y `python manage.py check` pasa.

---

# FASE 4 — URLs (`catalogo/urls.py`)

## Tarea 4.1 — Agregar las rutas

Añadir al `urlpatterns` existente (sin alterar las rutas de libros ni del home):

```python
path('authors/', views.AuthorListView.as_view(), name='authors'),
path('author/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
```

## Tarea 4.2 — Consistencia con `get_absolute_url()`

El modelo `Author` ya declara:

```python
return reverse('author-detail', args=[str(self.id)])
```

Por lo tanto el `name` de la ruta de detalle **debe ser exactamente** `author-detail`. Si se le pone otro nombre, `get_absolute_url()` truena con `NoReverseMatch`.

**Criterio de aceptación Fase 4:**
- `http://127.0.0.1:8000/catalogo/authors/` (o la ruta base que ya use el proyecto) responde 200.
- `{% url 'authors' %}` y `{% url 'author-detail' author.pk %}` resuelven sin error.

---

# FASE 5 — Plantillas HTML

## Tarea 5.1 — `author_list.html`

Requisitos:
- Extender de la plantilla maestra: `{% extends "catalogo/pagina_maestra.html" %}` (ajustar la ruta a como la extienden `book_list.html`).
- Bloque de contenido con el mismo nombre de bloque que usan las plantillas de libros.
- Tabla Bootstrap 5 (`table table-striped table-hover` o las clases ya usadas en la tabla de libros).
- Columnas sugeridas: **Apellido(s), Nombre(s), Seudónimo, Nacionalidad, Acciones**.
- Columna "Acciones" con un botón/enlace **Ver** apuntando al detalle.
- Manejo del caso vacío (`{% empty %}`) con un mensaje tipo "No hay autores registrados".
- Mostrar `—` o "N/A" cuando `pen_name` sea nulo (usar `{{ author.pen_name|default:"—" }}`).

Estructura de referencia:

```html
{% extends "catalogo/pagina_maestra.html" %}

{% block content %}
<h1 class="mb-4">Lista de autores</h1>

<table class="table table-striped table-hover align-middle">
  <thead>
    <tr>
      <th>Apellidos</th>
      <th>Nombre</th>
      <th>Seudónimo</th>
      <th>Nacionalidad</th>
      <th>Acciones</th>
    </tr>
  </thead>
  <tbody>
    {% for author in author_list %}
    <tr>
      <td>{{ author.last_name }}</td>
      <td>{{ author.first_name }}</td>
      <td>{{ author.pen_name|default:"—" }}</td>
      <td>{{ author.nationality }}</td>
      <td>
        <a class="btn btn-sm btn-primary" href="{% url 'author-detail' author.pk %}">Ver</a>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="5" class="text-center">No hay autores registrados.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

> Si la vista usa paginación, agregar el mismo bloque de paginación que ya tiene `book_list.html`.

## Tarea 5.2 — `author_detail.html`

Requisitos:
- Extender de `pagina_maestra.html`.
- Mostrar: **Nombre completo, Seudónimo, Nacionalidad**. Incluir también fecha de nacimiento y de fallecimiento si el detalle de libro sigue ese nivel de detalle.
- Usar una `card` de Bootstrap 5, consistente con `book_detail.html`.
- Enlace "Volver a la lista" apuntando a `{% url 'authors' %}`.

Estructura de referencia:

```html
{% extends "catalogo/pagina_maestra.html" %}

{% block content %}
<div class="card shadow-sm">
  <div class="card-body">
    <h2 class="card-title">{{ author.first_name }} {{ author.last_name }}</h2>
    <p><strong>Seudónimo:</strong> {{ author.pen_name|default:"—" }}</p>
    <p><strong>Nacionalidad:</strong> {{ author.nationality }}</p>
    <p><strong>Fecha de nacimiento:</strong> {{ author.date_of_birth|default:"—" }}</p>
    <p><strong>Fecha de fallecimiento:</strong> {{ author.date_of_death|default:"—" }}</p>

    <hr>
    <h5>Libros de este autor</h5>
    <ul class="list-group list-group-flush">
      {% for book in author.book_set.all %}
        <li class="list-group-item">
          <a href="{% url 'book-detail' book.pk %}">{{ book.title }}</a>
        </li>
      {% empty %}
        <li class="list-group-item">Este autor no tiene libros registrados.</li>
      {% endfor %}
    </ul>

    <a class="btn btn-secondary mt-3" href="{% url 'authors' %}">Volver a la lista</a>
  </div>
</div>
{% endblock %}
```

### Nota sobre la relación inversa (reto de reflexión)
`author.book_set.all` funciona porque `Book.author` es un `ForeignKey` hacia `Author` **sin** `related_name`, por lo que Django genera el accesor por defecto `<modelo_en_minúsculas>_set`. Si en algún momento se agrega `related_name='books'` al FK, el template debe usar `author.books.all`.

> El nombre de la ruta de detalle de libro (`book-detail`) debe coincidir con el que ya existe en el proyecto; verificar antes de usarlo en el template.

## Tarea 5.3 — Enlazar el menú en `pagina_maestra.html`

**Cambio mínimo y único** en la plantilla maestra: localizar la opción "Lista de autores" dentro del dropdown de Catálogos y reemplazar:

```html
<a class="dropdown-item" href="#">Lista de autores</a>
```

por:

```html
<a class="dropdown-item" href="{% url 'authors' %}">Lista de autores</a>
```

No modificar ninguna otra entrada del navbar ni la estructura del dropdown.

**Criterio de aceptación Fase 5:**
- Las dos plantillas nuevas heredan correctamente la maestra (se ve el navbar y el estilo Bootstrap).
- El menú "Catálogos → Lista de autores" navega a la lista.
- El botón "Ver" navega al detalle del autor correcto.

---

# FASE 6 — Pruebas y evidencias

## Tarea 6.1 — Pruebas funcionales

- [ ] Crear 2–3 autores desde el admin, llenando `pen_name` en unos y dejándolo vacío en otros, y `nationality` en todos.
- [ ] Verificar que el admin no truena al guardar (los campos nuevos aparecen en el formulario).
- [ ] `/authors/` muestra la tabla con todos los autores.
- [ ] El autor sin seudónimo muestra `—` y no un valor vacío raro ni `None`.
- [ ] El detalle muestra los datos correctos y lista los libros del autor.
- [ ] Un autor sin libros muestra el mensaje de lista vacía y no rompe la página.
- [ ] `/author/9999/` (id inexistente) devuelve 404 y no un error 500.
- [ ] El contador de autores en el Home coincide con el número real de registros.

## Tarea 6.2 — Capturas de pantalla requeridas para el reporte

**Código y configuración:**
1. `models.py` — clase `Author` completa mostrando `first_name`, `last_name` (max_length=40), `pen_name` y `nationality`.
2. Terminal — ejecución de `makemigrations` mostrando cómo se resolvió el valor por defecto de `nationality`, y la ejecución exitosa de `migrate`.
3. `urls.py` — las rutas `authors` y `author-detail`.
4. `views.py` — `AuthorListView` y `AuthorDetailView`.

**Interfaz de usuario:**
5. Página de Inicio con la tarjeta del contador de autores actualizado.
6. Menú desplegable "Catálogos" abierto, mostrando la opción "Lista de autores" ya enlazada.
7. Tabla de lista de autores renderizada con Bootstrap 5.
8. Vista de detalle de un autor individual.

---

## Checklist global de la versión 2

- [ ] **Fase 1** — Modelo `Author` con `max_length=40`, `pen_name` opcional y `nationality` obligatorio
- [ ] **Fase 2** — Migración generada resolviendo el default de `nationality`, aplicada en MySQL sin pérdida de datos
- [ ] **Fase 3** — `AuthorListView` y `AuthorDetailView` creadas; contador de autores en el home
- [ ] **Fase 4** — Rutas `authors` y `author-detail` registradas (nombre exacto por `get_absolute_url`)
- [ ] **Fase 5** — `author_list.html` y `author_detail.html` creadas; `href="#"` del menú reemplazado por `{% url 'authors' %}`
- [ ] **Fase 6** — Pruebas funcionales pasadas y 8 capturas de evidencia tomadas

**Definición de "hecho" para la v2:** el servidor corre sin errores, el menú "Catálogos → Lista de autores" lleva a una tabla Bootstrap con los autores (seudónimo y nacionalidad incluidos), el botón "Ver" abre el detalle del autor con sus libros asociados, y nada de lo implementado en la v1 (libros, admin, home) dejó de funcionar.
