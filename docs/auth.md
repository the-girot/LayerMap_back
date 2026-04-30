# Аутентификация и авторизация

> JWT-аутентификация через fastapi-users с cookie-транспортом и ролевой ACL на уровне проектов.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/core/auth.py` | FastAPIUsers, JWT strategy, CookieTransport, ACL-зависимости |
| `app/core/security.py` | Вспомогательные функции: хеширование, создание/декодирование JWT |
| `app/core/user_manager.py` | UserManager — хуки жизненного цикла пользователя |
| `app/routers/auth.py` | Роутер аутентификации (фабрика) |
| `app/services/users.py` | Сервис работы с пользователями |

## Как устроено

### Аутентификация

```
CookieTransport (layermap_access) ←→ JWTStrategy (HS256)
                                      │
                              fastapi_users[User, int]
                                      │
                              ┌───────┴───────┐
                         current_active_user  current_superuser
```

- **Транспорт**: Cookie (`layermap_access`), HttpOnly, SameSite=Lax
- **Стратегия**: JWT (HS256) с настраиваемым TTL
- **Библиотека**: fastapi-users с кастомным UserManager

### Авторизация (ACL)

Ролевая модель на уровне проектов:

```
ProjectRole:
  owner   = "owner"    (полный доступ)
  editor  = "editor"   (чтение + запись)
  viewer  = "viewer"   (только чтение)
```

Иерархия прав проверяется фабрикой `require_project_role`:

```python
def require_project_role(required_role: ProjectRole):
    # 1. Загружает проект (404 если нет)
    # 2. Superuser — полный доступ
    # 3. Проверяет membership пользователя в проекте
    # 4. Сравнивает уровни: owner > editor > viewer
```

Использование в роутерах:

```python
ProjectViewer = Annotated[Project, Depends(require_project_role(ProjectRole.viewer))]
ProjectEditor = Annotated[Project, Depends(require_project_role(ProjectRole.editor))]
ProjectOwner = Annotated[Project, Depends(require_project_role(ProjectRole.owner))]
```

### Эндпоинты аутентификации

| Метод | Путь | Описание |
|-------|------|---------|
| POST | `/auth/jwt/login` | Вход (JWT в cookie) |
| POST | `/auth/register` | Регистрация |
| POST | `/auth/forgot-password` | Запрос сброса пароля |
| POST | `/auth/reset-password` | Сброс пароля |
| GET | `/users/me` | Текущий пользователь |
| PATCH | `/users/me` | Обновление профиля |
| GET | `/users/{id}` | Получение пользователя (админ) |
| PATCH | `/users/{id}` | Обновление пользователя (админ) |
| DELETE | `/users/{id}` | Удаление пользователя (админ) |

## Ключевые сущности

- **`fastapi_users[User, int]`** — центральный объект библиотеки
- **`current_active_user` / `current_superuser`** — FastAPI-зависимости
- **`require_project_role(role)`** — фабрика ACL-зависимости
- **`ProjectRole`** — enum: owner, editor, viewer
- **`UserManager`** — хуки: `on_after_register`, `on_after_forgot_password`

## Как использовать / запустить

```python
# В роутере — проверка прав
@router.get("/projects/{project_id}")
async def get_project(
    _: CurrentUser,               # аутентификация
    project: ProjectEditor,        # авторизация (editor+)
    db: DBSession,
):
    ...
```

## Связи с другими доменами

- [config.md](config.md) — JWT секреты, cookie-настройки
- [users.md](users.md) — User модель, user_manager.py
- [database.md](database.md) — ProjectMember модель для ACL
- [api.md](api.md) — зависимости CurrentUser, ProjectViewer/Editor/Owner в роутерах
- [tests.md](tests.md) — тесты безопасности (test_security_api.py)

## Нюансы и ограничения

- **ACL применяется не на всех эндпоинтах** — в проектах есть эндпоинты только с `CurrentUser` без проверки роли (технический долг)
- `ProjectMember` создаётся только через сервис `projects.create()` (создатель становится owner)
- Нет отдельного эндпоинта для управления участниками проекта (invite/remove member)
- В production должна быть интеграция с email для сброса пароля
