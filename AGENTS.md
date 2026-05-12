# PROJECT: [Uppy file upload widget and companion for Django]

## Development Commands

- **Run server**: `uv run python manage.py runserver`
- **Run tests**: `uv run pytest`
- **Django shell**: `uv run python manage.py shell`

## Architecture Notes

- Django 5.2+ with Python 3.12+
- Uses `django` for web framework
- Uses `djangorestframework` for API
- Uses `pytest` for testing

## Architecture Rules

- Always use DRY (Don't Repeat Yourself) principles
- Always use clean code principles

## Forbidden Patterns

- **NEVER** use bare `except Exception: pass`
- **NEVER** use catch all exceptions `except Exception:` or `except:` blocks
