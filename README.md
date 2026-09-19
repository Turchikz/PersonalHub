# PersonalHub

PersonalHub — учебный Django-проект для разработки и тестирования полезных повседневных инструментов. Первый модуль, `metrology`, помогает вести учёт средств измерений и их поверок.

## Возможности

- Учёт средств измерений и истории их поверок.
- REST API для создания, просмотра, изменения и удаления записей.
- Проверка дат поверки и позиции средства измерений в зависимости от его статуса.
- Защита от удаления средства измерений, у которого есть поверки.
- Фильтрация приборов по статусу и функциональному узлу, поверок — по средству измерений.
- Автоматические тесты и проверка pull request через GitHub Actions.

## Стек

Python, Django, Django REST Framework, django-filter, pytest и pytest-django.

## Локальный запуск

```powershell
git clone https://github.com/Turchikz/PersonalHub.git
cd PersonalHub
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

После запуска открой [API](http://127.0.0.1:8000/api/).

## API

| Ресурс | Адрес | Фильтры |
| --- | --- | --- |
| Средства измерений | `/api/instruments/` | `status`, `functional_unit` |
| Поверки | `/api/verifications/` | `instrument` |

Примеры запросов:

```text
GET /api/instruments/?status=WORK
GET /api/instruments/?functional_unit=BIK&status=WORK
GET /api/verifications/?instrument=1
```

## Проверка

```powershell
python manage.py check
python -m pytest -v
```