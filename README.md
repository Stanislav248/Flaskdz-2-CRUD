# Flask CRUD: Бібліотека книг

Невеликий застосунок для обліку книг. Реалізовано всі чотири CRUD-операції.

| Операція | Маршрут | Метод |
|----------|---------|-------|
| Create | `/books/new` | GET (форма), POST (збереження) |
| Read (список + пошук) | `/` , `/?q=текст` | GET |
| Read (одна книга) | `/books/<id>` | GET |
| Update | `/books/<id>/edit` | GET (форма), POST (збереження) |
| Delete | `/books/<id>/delete` | POST |

Дані зберігаються в SQLite (файл `instance/books.db` створюється автоматично).

## Запуск (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Відкрийте http://127.0.0.1:5000
