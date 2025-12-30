# Django TODO App

This is a simple TODO application built with Django for the AI-Assisted Development homework.

## Features
- Create, edit, and delete TODOs
- Assign due dates
- Mark TODOs as resolved
- Admin panel for managing TODOs
- Unit tests for models and views

## Setup

1. **Install dependencies**

    Ensure you have Python 3.8+ and pip. Install Django:
    
    ```bash
    pip install django
    ```

2. **Run migrations**

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

3. **Run tests**

    ```bash
    python manage.py test
    ```

4. **Create a superuser (optional, for admin panel)**

    ```bash
    python manage.py createsuperuser
    ```

5. **Start the development server**

    ```bash
    python manage.py runserver
    ```

6. **Access the app**

    - TODO list: http://localhost:8000/
    - Admin: http://localhost:8000/admin/

## Project Structure

- `todos/` - App with models, views, templates, and tests
- `todo_project/` - Django project settings and URLs
- `templates/todos/` - HTML templates

## Testing

All core features are covered by unit tests in `todos/tests.py`.

## License

MIT License

## git

https://github.com/znyiri100/ai-dev-tools.git/01-todo
