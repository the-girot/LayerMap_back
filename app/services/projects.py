from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    PROJECTS_LIST_KEY,
    cache_delete,
    cache_get,
    cache_set,
    project_key,
    settings,
)
from app.core.utils import handle_integrity
from app.models.project import Project, ProjectStatus
from app.models.project_member import ProjectMember, ProjectRole
from app.schemas.project import (
    ProjectCreate,
    ProjectKPIOut,
    ProjectOut,
    ProjectSummaryOut,
    ProjectUpdate,
)
from app.services.users import get_project_member

# Ключи кэша списков и агрегатов по проектам.
# PROJECTS_LIST_KEY импортируется из app.core.cache
PROJECTS_KPI_KEY = "projects:kpi"
PROJECTS_RECENT_KEY = (
    "projects:recent"  # кэшируем один «дефолтный» список последних проектов
)


async def get_list(db: AsyncSession) -> list[Project]:
    """
    Return the list of all projects ordered by creation date (descending).

    The function сначала пытается прочитать результат из Redis-кэша по ключу
    ``PROJECTS_LIST_KEY``. Если кэш найден, возвращается список "отвязанных"
    ORM-объектов, восстановленных из сериализованных Pydantic-схем.

    Если кэш пустой:
    - выполняется SELECT к БД;
    - результат сериализуется в список словарей через `ProjectOut`;
    - сериализованный список сохраняется в Redis с TTL = 60 секунд;
    - вызывающему коду возвращаются "живые" ORM-объекты, привязанные к текущей сессии.

    Параметры:
        db: асинхронная SQLAlchemy-сессия.

    Возвращает:
        Список ORM-объектов Project в порядке от новых к старым.
    """
    cached = await cache_get(PROJECTS_LIST_KEY)
    if cached:
        # Восстанавливаем из dict обратно в ORM-объект без привязки к сессии.
        # Это безопасно для read-only сценариев.
        return [Project(**item) for item in cached]

    rows = (
        (await db.execute(select(Project).order_by(Project.created_at.desc())))
        .scalars()
        .all()
    )

    # Сериализуем только чистые поля, без internal SA-атрибутов.
    await cache_set(
        PROJECTS_LIST_KEY,
        [ProjectOut.model_validate(r).model_dump(mode="json") for r in rows],
        ttl=60,
    )
    return rows


async def get_one(db: AsyncSession, project_id: int) -> Project | None:
    """
    Return a single project by its identifier.

    Функция сначала читает объект проекта из Redis-кэша по ключу,
    сформированному через `project_key(project_id)`. Если кэш найден,
    возвращается "отвязанный" ORM-объект, восстановленный из словаря.

    Если в кэше ничего нет:
    - выполняется SELECT по первичному ключу;
    - при успехе результат сериализуется через `ProjectOut` и
      сохраняется в Redis с TTL = `settings.CACHE_TTL`.

    Параметры:
        db: асинхронная SQLAlchemy-сессия.
        project_id: идентификатор проекта.

    Возвращает:
        ORM-объект Project, если найден, иначе None.
    """
    key = project_key(project_id)
    cached = await cache_get(key)
    if cached:
        return Project(**cached)

    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()

    if obj:
        await cache_set(
            key,
            ProjectOut.model_validate(obj).model_dump(mode="json"),
            ttl=settings.CACHE_TTL,
        )
    return obj


async def get_kpi(db: AsyncSession) -> ProjectKPIOut:
    """
    KPI по проектам: всего, активные, черновики, архивные.
    Кэшируется отдельно от списка проектов.
    """
    cached = await cache_get(PROJECTS_KPI_KEY)
    if cached:
        return ProjectKPIOut(**cached)

    stmt = select(
        func.count().label("total"),
        func.count().filter(Project.status == ProjectStatus.active).label("active"),
        func.count().filter(Project.status == ProjectStatus.draft).label("draft"),
        func.count().filter(Project.status == ProjectStatus.archived).label("archived"),
    )
    row = (await db.execute(stmt)).one()

    kpi = ProjectKPIOut(
        total=row.total,
        active=row.active,
        draft=row.draft,
        archived=row.archived,
    )
    await cache_set(PROJECTS_KPI_KEY, kpi.model_dump(mode="json"), ttl=60)
    return kpi


async def get_recent(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    limit: int = 5,
) -> list[Project]:
    """
    Последние N проектов по updated_at.

    user_id оставляем на будущее (фильтр по доступности пользователю),
    сейчас он не используется, но уже есть в сигнатуре сервиса.
    """
    use_cache = user_id is None and limit == 5
    if use_cache:
        cached = await cache_get(PROJECTS_RECENT_KEY)
        if cached:
            return [Project(**item) for item in cached]

    stmt = select(Project)

    # TODO: когда появится ACL, добавить сюда фильтр по user_id/правам.
    # if user_id is not None:
    #     stmt = stmt.join(ProjectUser).where(ProjectUser.user_id == user_id)

    stmt = stmt.order_by(Project.updated_at.desc()).limit(limit)

    result = await db.execute(stmt)
    projects = result.scalars().all()

    if use_cache:
        await cache_set(
            PROJECTS_RECENT_KEY,
            [
                ProjectSummaryOut.model_validate(p).model_dump(mode="json")
                for p in projects
            ],
            ttl=60,
        )

    return projects


async def create(
    db: AsyncSession,
    payload: ProjectCreate,
    user_id: int,
) -> Project:
    """
    Create a new project and invalidate project-related caches.

    Шаги:
    - создать ORM-объект Project из входной Pydantic-схемы;
    - добавить его в сессию и попытаться закоммитить в контексте
      `handle_integrity`, который преобразует `IntegrityError` в 409;
    - после успешного коммита обновить объект через `db.refresh`;
    - добавить текущего пользователя как owner проекта;
    - удалить кэши:
        * общего списка проектов (PROJECTS_LIST_KEY);
        * KPI (PROJECTS_KPI_KEY);
        * списка последних проектов (PROJECTS_RECENT_KEY).

    Параметры:
        db: асинхронная SQLAlchemy-сессия.
        payload: данные нового проекта (имя, описание, статус и т.д.).
        user_id: ID пользователя, создающего проект.

    Возвращает:
        Созданный ORM-объект Project.
    """
    obj = Project(**payload.model_dump())
    db.add(obj)
    async with handle_integrity(
        db,
        "Проект с таким именем уже существует",
    ):
        await db.commit()

    await db.refresh(obj)

    # Добавить текущего пользователя как owner проекта
    member = ProjectMember(
        user_id=user_id,
        project_id=obj.id,
        role=ProjectRole.owner,
    )
    db.add(member)
    await db.commit()

    await cache_delete(PROJECTS_LIST_KEY, PROJECTS_KPI_KEY, PROJECTS_RECENT_KEY)
    return obj


async def update(
    db: AsyncSession,
    project_id: int,
    payload: ProjectUpdate,
) -> Project | None:
    """
    Update an existing project and invalidate project-related caches.

    Шаги:
    - загрузить проект по первичному ключу; если не найден — вернуть None;
    - применить patch: проставить только поля из payload, которые были указаны;
    - попытаться закоммитить изменения в контексте `handle_integrity`,
      чтобы перехватить возможный конфликт по уникальному имени;
    - после успешного коммита обновить объект через `db.refresh`;
    - удалить кэши:
        * конкретного проекта (project_key(project_id));
        * общего списка проектов;
        * KPI и списка последних проектов.

    Параметры:
        db: асинхронная SQLAlchemy-сессия.
        project_id: идентификатор проекта, который нужно обновить.
        payload: частичное обновление полей проекта.

    Возвращает:
        Обновлённый ORM-объект Project или None, если проект не найден.
    """
    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not obj:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    async with handle_integrity(
        db,
        "Проект с таким именем уже существует",
    ):
        await db.commit()

    await db.refresh(obj)
    await cache_delete(
        project_key(project_id),
        PROJECTS_LIST_KEY,
        PROJECTS_KPI_KEY,
        PROJECTS_RECENT_KEY,
    )
    return obj


async def delete(db: AsyncSession, project_id: int) -> bool:
    """
    Delete an existing project and invalidate project-related caches.

    Шаги:
    - загрузить проект по первичному ключу; если не найден — вернуть False;
    - удалить объект из сессии и закоммитить транзакцию;
    - удалить кэши:
        * конкретного проекта (project_key(project_id));
        * общего списка проектов;
        * KPI и списка последних проектов.

    Параметры:
        db: асинхронная SQLAlchemy-сессия.
        project_id: идентификатор проекта, который нужно удалить.

    Возвращает:
        True, если проект был найден и успешно удалён, иначе False.
    """
    obj = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if not obj:
        return False

    await db.delete(obj)
    await db.commit()
    await cache_delete(
        project_key(project_id),
        PROJECTS_LIST_KEY,
        PROJECTS_KPI_KEY,
        PROJECTS_RECENT_KEY,
    )
    return True


async def get_filtered_list(
    db: AsyncSession,
    *,
    status: ProjectStatus | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
) -> list[Project]:
    """
    Вернуть список проектов с фильтрами, поиском и пагинацией.

    Фильтры:
        - status: по статусу проекта (active/draft/archived).
        - search: подстрочный поиск по имени (case-insensitive).

    Пагинация:
        - page: номер страницы, начиная с 1.
        - size: размер страницы (количество проектов на странице).

    Сортировка:
        - sort_by: поле сортировки (сейчас поддерживаем только updated_at).
        - sort_dir: направление сортировки ('asc' или 'desc').
    """
    stmt = select(Project)

    if status is not None:
        stmt = stmt.where(Project.status == status)

    if search:
        # PostgreSQL: ILIKE для case-insensitive substring-поиска.
        pattern = f"%{search}%"
        stmt = stmt.where(Project.name.ilike(pattern))

    # Пока поддерживаем только сортировку по updated_at.
    order_column = Project.updated_at
    if sort_dir == "asc":
        stmt = stmt.order_by(order_column.asc())
    else:
        stmt = stmt.order_by(order_column.desc())

    offset = (page - 1) * size
    stmt = stmt.offset(offset).limit(size)

    result = await db.execute(stmt)
    return result.scalars().all()


async def check_owner_access(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> bool:
    """
    Проверить, является ли пользователь владельцем проекта.

    Параметры:
        db: асинхронная сессия БД.
        project_id: ID проекта.
        user_id: ID пользователя.

    Возвращает:
        True, если пользователь является владельцем проекта.
    """
    member = await get_project_member(db, user_id=user_id, project_id=project_id)
    if not member:
        return False
    return member.role == ProjectRole.owner


async def check_editor_access(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> bool:
    """
    Проверить, имеет ли пользователь права редактора или выше.

    Параметры:
        db: асинхронная сессия БД.
        project_id: ID проекта.
        user_id: ID пользователя.

    Возвращает:
        True, если пользователь имеет права editor или owner.
    """
    member = await get_project_member(db, user_id=user_id, project_id=project_id)
    if not member:
        return False
    return member.role in (ProjectRole.editor, ProjectRole.owner)


async def check_viewer_access(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> bool:
    """
    Проверить, имеет ли пользователь права зрителя или выше.

    Параметры:
        db: асинхронная сессия БД.
        project_id: ID проекта.
        user_id: ID пользователя.

    Возвращает:
        True, если пользователь имеет права viewer, editor или owner.
    """
    member = await get_project_member(db, user_id=user_id, project_id=project_id)
    return member is not None
