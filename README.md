# Django API Boilerplate

## 📌 Overview
This is a **Django REST Framework (DRF)** boilerplate for building scalable and modular APIs with JWT authentication, class-based views, and best practices.

## 📁 Project Structure
```
├── celerybeat-schedule.db
├── core
│   ├── asgi.py
│   ├── celery.py
│   ├── email.py
│   ├── __init__.py
│   ├── settings
│   │   ├── base.py
│   │   ├── __init__.py
│   │   ├── local.py
│   │   └── test.py
│   ├── tasks.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── openai_app
│   ├── admin.py
│   ├── api
│   │   ├── urls.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── permissions.py
│   │       ├── serializers.py
│   │       ├── tests.py
│   │       ├── urls.py
│   │       └── views.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── services
│   │   ├── client.py
│   │   ├── __init__.py
│   │   └── services.py
│   └── utils
├── poetry.lock
├── project
│   ├── admin.py
│   ├── api
│   │   ├── urls.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── permissions.py
│   │       ├── serializers.py
│   │       ├── tests.py
│   │       ├── urls.py
│   │       └── views.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   ├── models.py
│   ├── services
│   │   ├── client.py
│   │   └── services.py
│   ├── tests.py
│   ├── utils
│   │   ├── extract_file_embeded.py
│   │   └── __pycache__
│   │       └── extract_file_embeded.cpython-310.pyc
│   └── views.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── upload
└── users
├── token_generators.py
├── urls.py
├── utils.py
└── views.py

```

## ⚙️ Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone git@github.com:arslantoor/ai-linguistic.git
cd ai-linguistic
```
### 2️⃣ Create & Activate Virtual Environment
```bash
pip install -g poetry
poetry init
```
### 3️⃣ Install Dependencies
```bash
poetry install
```
### 4️⃣ Set Up Environment Variables
Create a **`.env`** file in the project root and add:
```ini
SECRET_KEY=your_secret_key
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
```

### 5️⃣ Run Migrations
```bash
poetry run python manage.py makemigrations accounts
poetry run python manage.py migrate
```

### 6️⃣ Create a Superuser
```bash
poetry run python manage.py createsuperuser
```

### 7️⃣ Start the Development Server
```bash
poetry run python manage.py runserver
```

## 🔐 Authentication
This project uses **JWT Authentication**. Use the following endpoints:
- **Signup:** `POST /api/auth/signup/`
- **Login:** `POST /api/auth/login/`
- **Get User by UUID:** `GET /api/accounts/{uuid}/`
- **Get All Users:** `GET /api/accounts/`

## 📜 API Documentation
Swagger API Docs are available at:
```
http://127.0.0.1:8000/
```

## 🚀 Deployment
To deploy, make sure to:
- Set `DEBUG=False` in `.env`
- Use a production-ready database (e.g., PostgreSQL)
- Configure a WSGI server (e.g., Gunicorn, uWSGI)

## 📜 License
This project is **MIT Licensed**.

