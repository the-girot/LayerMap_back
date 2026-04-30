# Пользователи

> Управление учётными записями пользователей, их членством в проектах и ролями.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/models/user.py` | ORM модель User (fastapi-users совместимая) |
| `app/models/project_member.py` | ORM модель ProjectMember + ProjectRole enum |
| `app/schemas/user.py` | Pydantic схемы UserRead, UserCreate, UserUpdate |
| `app/core/user_manager.py` | UserManager — хуки жизненного цикла |
| `app/services/users.py` | Сервис пользователей |

## Как устроено

### Модель User

Наследуется от `SQLAlchemyBaseUserTable[int]` (fastapi-users), добавляет кастомные поля:

```python
class User(SQLAlchemyBaseUserTable[int], Base):
    id: int                    # primary key
    email: str                 # unique, indexed
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    # Кастомные поля
    full_name: str | None
    created_at: datetime
    updated_at: datetime
    # Relationships
    project_memberships → ProjectMember[]
```

### Членство в проектах

```python
class ProjectRole(enum.StrEnum):
    owner = "owner"    # полный доступ
    editor = "editor"  # чтение + запись
    viewer = "viewer"  # только чтение

class ProjectMember(Base):
    user_id: int       # FK → users
    project_id: int    # FK → projects
    role: ProjectRole  # owner | editor | viewer
    # UniqueConstraint(user_id, project_id)
```

### UserManager

Хуки от fastapi-users:

- **`on_after_register`** — логирует регистрацию
- **`on_after_forgot_password`** — логирует токен сброса (в production — отправка email)

## Связи с другими доменами

- [database.md](database.md) — модели User, ProjectMember
- [auth.md](auth.md) — аутентификация, ACL зависимости
- [projects.md](projects.md) — членство в проектах
- [api.md](api.md) — схемы UserRead, UserCreate, UserUpdate

## Нюансы и ограничения

- **Нет эндпоинта для управления участниками проекта** — owner назначается только при создании проекта; нет invite/remove/kick
- `UserManager` не интегрирован с email-сервисом — сброс пароля и верификация логируются, но не отправляются
- `full_name` — единственное кастомное поле поверх fastapi-users
- Модель User не имеет прямых связей с RPI, Source и т.д. — только через ProjectMember
