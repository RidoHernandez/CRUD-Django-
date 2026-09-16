# Django Catalog CRUD & Admin Customization

A basic Django web application that sets up a book catalog system connected to a MySQL database, featuring customized Django Admin components and automated CRUD modules.

## Features

- **Virtual Environment Setup:** Isolated environment for package management.
- **MySQL Integration:** Database configuration replacement for SQLite.
- **Model Migrations:** Automated database schema updates via Django ORM.
- **Superuser Management:** Admin authentication and authorization setup.
- **Custom Admin Interface:** Enhanced book list display with tabular views and choice-based dropdown inputs for languages.

## Getting Started

### Prerequisites

- Python 3.x
- MySQL Server

### Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
   cd your-repo-name

   Create and activate a virtual environment:

Bash
python -m venv entorno
# Windows
.\entorno\Scripts\activate
# macOS/Linux
source entorno/bin/activate
Install dependencies:

Bash
pip install django pymysql mysqlclient
Configure your database settings in BibliotecaProy/settings.py:

Python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
Apply migrations:

Bash
python manage.py makemigrations
python manage.py migrate
Create a superuser to access the admin panel:

Bash
python manage.py createsuperuser
Run the development server:

Bash
python manage.py runserver
Open http://127.0.0.1:8000/admin/ in your browser to manage the catalog.
