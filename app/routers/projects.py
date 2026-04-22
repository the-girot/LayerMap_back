
from fastapi import APIRouter, HTTPException, Query

from app.core.auth import CurrentUser, ProjectEditor, ProjectOwner, ProjectViewer
from app.database import DBSession
from app.models.project import ProjectStatus
from app.schemas.project import (
    ProjectCreate,
    ProjectKPIOut,
    ProjectOut,
    ProjectSummaryOut,
    ProjectUpdate,
)
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    db: DBSession,
    current_user: CurrentUser,  # ← только алиас
    status: ProjectStatus | None = Query(
        default=None,
        description="Фильтр по статусу проекта (active/draft/archived)",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        description="Поиск по подстроке в названии (case-insensitive)",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Номер страницы (начиная с 1)",
    ),
    size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Размер страницы (количество проектов на странице)",
    ),
    sort_by: str = Query(
        default="updated_at",
        description="Поле сортировки (пока поддерживается только 'updated_at')",
    ),
    sort_dir: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Направление сортировки: 'asc' или 'desc'",
    ),
):
    projects = await svc.get_filtered_list(
        db,
        status=status,
        search=search,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return [
        ProjectOut(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.get("/kpi", response_model=ProjectKPIOut)
async def get_projects_kpi(
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Получить агрегированные KPI по проектам для главной страницы.

    Эндпоинт возвращает:
    - общее количество проектов;
    - количество активных проектов;
    - количество проектов в статусе черновика;
    - количество архивных проектов.

    Значение кэшируется в Redis через сервисный слой (`svc.get_kpi`) с коротким TTL,
    чтобы не пересчитывать агрегаты при каждом запросе дашборда.

    Параметры:
        db: асинхронная сессия БД.
        current_user: текущий аутентифицированный пользователь.

    Возвращает:
        Объект `ProjectKPIOut`.
    """
    return await svc.get_kpi(db)


@router.get("/recent", response_model=list[ProjectSummaryOut])
async def get_recent_projects(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(5, ge=1, le=50, description="Максимальное количество проектов"),
):
    """
    Получить список последних изменённых проектов.

    Эндпоинт предназначен для главной страницы дашборда и возвращает краткую
    информацию по проектам:
    - id, name, status, updated_at;
    - отсортированную по updated_at в порядке убывания;
    - ограниченную параметром ``limit`` (по умолчанию 5).

    Для дефолтного значения limit сервисный слой использует Redis-кэш
    (`svc.get_recent`), для остальных значений всегда выполняется запрос к БД.

    Параметры:
        db: асинхронная сессия БД.
        current_user: текущий аутентифицированный пользователь.
        limit: максимальное число проектов (1–50, по умолчанию 5).

    Возвращает:
        Список объектов `ProjectSummaryOut`.
    """
    projects = await svc.get_recent(db, user_id=current_user.id, limit=limit)
    return [
        ProjectSummaryOut(
            id=p.id,
            name=p.name,
            status=p.status,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project: ProjectViewer,
    current_user: CurrentUser,
) -> ProjectOut:
    """
    Получить детали конкретного проекта по идентификатору.

    Проект предварительно загружается через зависимость `ProjectViewer`,
    которая проверяет, что пользователь имеет доступ к проекту (viewer или выше).

    Параметры:
        project: валидный проект с проверкой доступа.
        current_user: текущий аутентифицированный пользователь.

    Возвращает:
        Объект `ProjectOut` с полным набором полей.
    """
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Создать новый проект.

    Делегирует создание в сервисный слой (`svc.create`), где:
    - создаётся ORM-объект `Project` из входной схемы `ProjectCreate`;
    - выполняется коммит в БД с обработкой `IntegrityError` (409 при дубликате имени);
    - текущий пользователь добавляется как owner проекта;
    - инвалидируются кэши списка проектов, KPI и последних проектов.

    Параметры:
        payload: данные нового проекта (имя, описание, статус).
        db: асинхронная сессия БД.
        current_user: текущий аутентифицированный пользователь.

    Возвращает:
        Объект `ProjectOut` для созданного проекта.
    """
    obj = await svc.create(db, payload, user_id=current_user.id)
    return ProjectOut(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    payload: ProjectUpdate,
    project: ProjectEditor,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Обновить существующий проект.

    Шаги:
    - через зависимость `ProjectEditor` убеждаемся, что пользователь имеет права editor или выше;
    - передаём частичное обновление в `svc.update`, который применяет PATCH и
      обрабатывает возможный конфликт уникальности имени;
    - после успешного обновления инвалидируются кэши проекта, списка, KPI и последних проектов.

    Параметры:
        payload: частичное обновление полей проекта.
        project: текущий проект с проверкой доступа (editor или выше).
        current_user: текущий аутентифицированный пользователь.
        db: асинхронная сессия БД.

    Возвращает:
        Объект `ProjectOut` для обновлённого проекта.

    Исключения:
        HTTPException 403: если у пользователя нет прав editor или выше.
        HTTPException 404: если проект не найден (дополнительная проверка на случай
        состязательных условий).
    """
    obj = await svc.update(db, project.id, payload)
    if not obj:
        raise HTTPException(404, "Проект не найден")
    return ProjectOut(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        status=obj.status,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project: ProjectOwner,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Удалить проект по идентификатору.

    Проект предварительно загружается через `ProjectOwner` (403, если у пользователя нет прав owner),
    после чего сервисный слой выполняет физическое удаление и инвалидацию
    кэшей проекта, списка проектов, KPI и последних проектов.

    Параметры:
        project: валидный проект с проверкой доступа (owner).
        current_user: текущий аутентифицированный пользователь.
        db: асинхронная сессия БД.

    Возвращает:
        Ничего (HTTP 204 No Content при успехе).

    Исключения:
        HTTPException 403: если у пользователя нет прав owner.
    """
    await svc.delete(db, project.id)
