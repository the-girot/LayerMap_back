# LayerMap Back - Project Documentation

## 1. Project Overview

**Project Name:** LayerMap Back (layermap-back)

**Description:** LayerMap Back is a backend API service for managing RPI (Reporting and Planning Integration) mappings in a multi-project environment. The application provides a structured way to define, track, and manage data mappings between source systems and target reporting objects. It supports role-based access control for projects, allowing multiple users to collaborate on mapping initiatives with different permission levels (viewer, editor, owner). The system is designed for enterprise reporting scenarios where data lineage, ownership, and approval workflows are critical.

**Technology Stack:**
- **Language:** Python 3.13+
- **Web Framework:** FastAPI 0.111+
- **Database:** PostgreSQL 16+ with SQLAlchemy 2.0 (async)
- **Database Driver:** asyncpg 0.29+
- **Cache:** Redis 7+ (async support via redis[asyncio] 5.0+)
- **Authentication:** JWT (python-jose 3.5+) with bcrypt password hashing
- **Validation:** Pydantic 2.7+
- **Migrations:** Alembic 1.13+
- **Testing:** pytest 9.0+ with pytest-asyncio, httpx for async client
- **Server:** Uvicorn 0.29+ (ASGI)
- **Linting/Formatting:** Ruff 0.15+

**Architecture Summary:**
The application follows a **layered monolith** architecture with clear separation of concerns:
- **Router Layer** (`app/routers/`): HTTP endpoint definitions, request/response schema validation
- **Service Layer** (`app/services/`): Business logic, database operations, cache invalidation
- **Model Layer** (`app/models/`): SQLAlchemy ORM models with relationships
- **Schema Layer** (`app/schemas/`): Pydantic models for request/response validation
- **Core Layer** (`app/core/`): Cross-cutting concerns (auth, security, cache, config)
- **Database Layer** (`app/database.py`): Session management, engine configuration

**Key Design Patterns:**
- **Dependency Injection:** FastAPI `Depends()` for database sessions, authentication, and authorization
- **Repository Pattern:** Service layer encapsulates all data access logic
- **Cache-Aside Pattern:** Redis caching with explicit invalidation on writes
- **CQRS-lite:** Separate read paths (cached) from write paths (direct DB)
- **ACL (Access Control List):** Role-based permissions (viewer/editor/owner) enforced via dependencies

**High-Level Component Diagram:**

```mermaid
graph TB
    Client[HTTP Client] -->|REST API| LB[Load Balancer]
    LB --> API[FastAPI Server]
    
    subgraph "Application Layer"
        API --> Router[Router Layer]
        Router --> Service[Service Layer]
        Service --> ORM[SQLAlchemy ORM]
    end
    
    subgraph "Data Layer"
        ORM -->|Async| PG[(PostgreSQL)]
        Service -->|Cache| Redis[(Redis)]
    end
    
    subgraph "Security"
        JWT[JWT Token] --> Auth[Authentication]
        ACL[Role Check] --> Auth
    end
    
    API -.-> Auth
    Auth -.-> Service
```

---

## 2. Getting Started

### Prerequisites

- **Python:** 3.13 or higher
- **PostgreSQL:** 16 or higher (or use Docker Compose)
- **Redis:** 7 or higher (or use Docker Compose)
- **Git:** For cloning the repository

### Step-by-Step Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd LayerMap_back
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or using pyproject.toml:
   pip install -e .
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rpi_db
   REDIS_URL=redis://localhost:6379/0
   CACHE_TTL=300
   REDIS_MAX_CONNECTIONS=200
   APP_TITLE=RPI Mapping API
   APP_VERSION=1.0.0
   DEBUG=False
   CORS_ORIGINS=["http://localhost:5173"]
   JWT_SECRET_KEY=your-super-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Start PostgreSQL and Redis (using Docker Compose):**
   ```bash
   docker-compose up -d postgres redis
   ```

6. **Run database migrations:**
   ```bash
   cd alembic
   alembic upgrade head
   cd ..
   ```

7. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Verify the installation:**
   Open http://localhost:8000/docs for the Swagger UI documentation.

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:password@localhost/rpi_db` | PostgreSQL connection string with asyncpg driver |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_TTL` | No | `300` | Default cache time-to-live in seconds |
| `REDIS_MAX_CONNECTIONS` | No | `200` | Maximum Redis connection pool size |
| `APP_TITLE` | No | `RPI Mapping API` | API title for documentation |
| `APP_VERSION` | No | `1.0.0` | API version string |
| `DEBUG` | No | `False` | Enable debug mode (SQL echo, etc.) |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | List of allowed CORS origins (JSON array or comma-separated) |
| `JWT_SECRET_KEY` | Yes | `your-super-secret-key-change-in-production` | Secret key for JWT signing (change in production!) |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm (HS256, RS256, etc.) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token expiration time in minutes |

---

## 3. Project Structure

```
LayerMap_back/
├── .github/                    # GitHub workflows (if any)
├── .pytest_cache/              # pytest cache directory
├── .ruff_cache/                # ruff linter cache
├── alembic/                    # Database migrations
│   ├── env.py                  # Alembic configuration
│   ├── script.py.mako          # Migration template
│   ├── versions/               # Migration scripts
│   │   ├── 94aca1390145_init.py              # Initial schema
│   │   ├── 35bc1c36160b_unique_proj_name.py  # Unique constraint on project name
│   │   ├── 4e3b3c8b6212_fix_source.py        # Source table fix
│   │   ├── 965613165dd4_fix_mapping_table.py # Mapping table fix
│   │   ├── ac218a78dc1f_fix_mapping_table_source_fk.py # FK fix
│   │   └── f50fdec921f8_fix_circular_fk.py   # Circular FK resolution
├── app/                        # Main application package
│   ├── core/                   # Core utilities and cross-cutting concerns
│   │   ├── auth.py             # Authentication and authorization dependencies
│   │   ├── cache.py            # Redis cache management
│   │   ├── config.py           # Application settings and configuration
│   │   ├── dependencies.py     # FastAPI dependency functions
│   │   ├── middleware.py       # Custom middleware (CORS)
│   │   ├── security.py         # Password hashing, JWT operations
│   │   └── utils.py            # Utility functions
│   ├── database.py             # SQLAlchemy engine and session management
│   ├── main.py                 # FastAPI application factory
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── mapping_table.py    # MappingTable and MappingColumn models
│   │   ├── project.py          # Project model
│   │   ├── project_member.py   # ProjectMember model (role assignments)
│   │   ├── rpi_mapping.py      # RPIMapping model
│   │   ├── source.py           # Source model
│   │   └── user.py             # User model
│   ├── routers/                # API route definitions
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── mapping_tables.py   # Mapping tables and columns endpoints
│   │   ├── projects.py         # Projects endpoints
│   │   ├── rpi_mappings.py     # RPI mappings endpoints
│   │   └── sources.py          # Sources endpoints
│   ├── schemas/                # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   ├── mapping_table.py    # MappingTable/Column schemas
│   │   ├── project.py          # Project schemas
│   │   ├── rpi_mapping.py      # RPIMapping schemas
│   │   ├── source.py           # Source schemas
│   │   └── user.py             # User schemas
│   └── services/               # Business logic layer
│       ├── __init__.py
│       ├── mapping_tables.py   # Mapping table business logic
│       ├── projects.py         # Project business logic
│       ├── rpi_mappings.py     # RPI mapping business logic
│       ├── sources.py          # Source business logic
│       └── users.py            # User business logic
├── tests/                      # Test suite
│   ├── conftest.py             # pytest fixtures and configuration
│   ├── factories.py            # Test data factories
│   ├── test_health.py          # Health check tests
│   ├── test_contract.py        # API contract tests
│   ├── test_errors.py          # Error handling tests
│   ├── test_functional_enhanced.py  # Functional tests
│   ├── test_integration.py     # Integration tests
│   ├── test_mapping_tables_api.py  # Mapping tables API tests
│   ├── test_performance_api.py     # Performance tests
│   ├── test_projects_api.py    # Projects API tests
│   ├── test_rpi_mappings_api.py    # RPI mappings API tests
│   ├── test_security_api.py    # Security API tests
│   ├── test_sources_api.py     # Sources API tests
│   ├── test_validation.py      # Validation tests
│   └── utils.py                # Test utilities
├── .env                        # Environment variables (not in VCS)
├── .gitignore                  # Git ignore rules
├── .python-version             # Python version specification
├── docker-compose.yaml         # Docker Compose configuration
├── pyproject.toml              # Project metadata and tool configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Project README
```

**Key Files and Their Responsibility:**

| File | Responsibility |
|------|----------------|
| [`app/main.py`](app/main.py:1) | FastAPI application factory, router registration, lifespan events |
| [`app/database.py`](app/database.py:1) | SQLAlchemy async engine, session factory, `DBSession` type alias |
| [`app/core/config.py`](app/core/config.py:1) | Pydantic settings class loading from `.env` file |
| [`app/core/auth.py`](app/core/auth.py:1) | JWT authentication, role-based authorization dependencies |
| [`app/core/cache.py`](app/core/cache.py:1) | Redis cache operations, key generation, TTL management |
| [`app/core/security.py`](app/core/security.py:1) | Password hashing (bcrypt), JWT token creation/verification |
| [`alembic/env.py`](alembic/env.py:1) | Alembic migration configuration and execution |

---

## 4. API / Routes Reference

### Authentication Endpoints

#### POST /auth/login

**Description:** User login using OAuth2 password flow (for Swagger UI). Accepts form-data with `username` (email) and `password` fields.

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| username | form | string | Yes | User email address |
| password | form | string | Yes | User password |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT token for authentication |
| token_type | string | Always "bearer" |

**Example request:**
```http
POST /auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=test@example.com&password=password123
```

**Example response:**
```json
{ "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer" }
```

**Error codes:** 401 — invalid credentials, 403 — user inactive

---

#### POST /auth/login/json

**Description:** User login using JSON payload (for frontend clients).

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| email | body | string | Yes | User email address |
| password | body | string | Yes | User password |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT token for authentication |
| token_type | string | Always "bearer" |

**Example request:**
```http
POST /auth/login/json HTTP/1.1
Content-Type: application/json

{ "email": "test@example.com", "password": "password123" }
```

**Example response:**
```json
{ "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer" }
```

**Error codes:** 401 — invalid credentials, 403 — user inactive

---

#### POST /auth/register

**Description:** Register a new user account.

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| email | body | string (email) | Yes | User email address |
| full_name | body | string | No | User's full name |
| password | body | string | Yes | Password (min 8 characters) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | User ID |
| email | string | User email |
| full_name | string | User full name |
| is_active | boolean | Whether user is active |
| is_superuser | boolean | Whether user is superuser |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{ "email": "new@example.com", "full_name": "New User", "password": "password123" }
```

**Example response:**
```json
{ "id": 2, "email": "new@example.com", "full_name": "New User", "is_active": true, "is_superuser": false, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 409 — email already exists

---

#### GET /auth/me

**Description:** Get current authenticated user information.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | header | string | Yes | Bearer JWT token |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | User ID |
| email | string | User email |
| full_name | string | User full name |
| is_active | boolean | Whether user is active |
| is_superuser | boolean | Whether user is superuser |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example response:**
```json
{ "id": 1, "email": "test@example.com", "full_name": "Test User", "is_active": true, "is_superuser": true, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — user inactive

---

### Projects Endpoints

#### GET /projects

**Description:** List all projects with optional filtering, search, and pagination.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| status | query | string | No | Filter by status: active, draft, archived |
| search | query | string | No | Case-insensitive substring search in name |
| page | query | integer | No | Page number (default: 1) |
| size | query | integer | No | Items per page (default: 20, max: 100) |
| sort_by | query | string | No | Sort field (currently only "updated_at") |
| sort_dir | query | string | No | Sort direction: asc or desc (default: desc) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects?status=active&page=1&size=10 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "name": "Project A", "description": "Desc", "status": "active", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
]
```

**Error codes:** 401 — unauthorized

---

#### GET /projects/kpi

**Description:** Get aggregated KPI statistics for the dashboard.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | header | string | Yes | Bearer JWT token |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| total | integer | Total number of projects |
| active | integer | Number of active projects |
| draft | integer | Number of draft projects |
| archived | integer | Number of archived projects |

**Example request:**
```http
GET /projects/kpi HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "total": 10, "active": 5, "draft": 3, "archived": 2 }
```

**Error codes:** 401 — unauthorized

---

#### GET /projects/recent

**Description:** Get the most recently updated projects.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| limit | query | integer | No | Max projects to return (default: 5, max: 50) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Project ID |
| name | string | Project name |
| status | string | Project status |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/recent?limit=10 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "name": "Project A", "status": "active", "updated_at": "2024-01-02T00:00:00Z" }
]
```

**Error codes:** 401 — unauthorized

---

#### GET /projects/{project_id}

**Description:** Get a specific project by ID.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "id": 1, "name": "Project A", "description": "Desc", "status": "active", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### POST /projects

**Description:** Create a new project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| name | body | string | Yes | Project name (unique) |
| description | body | string | No | Project description |
| status | body | string | No | Project status: active, draft, archived (default: draft) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /projects HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "name": "New Project", "description": "Description", "status": "active" }
```

**Example response:**
```json
{ "id": 2, "name": "New Project", "description": "Description", "status": "active", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 409 — project name already exists

---

#### PATCH /projects/{project_id}

**Description:** Update an existing project (partial update).

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| name | body | string | No | New project name |
| description | body | string | No | New project description |
| status | body | string | No | New project status |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PATCH /projects/1 HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "status": "archived" }
```

**Example response:**
```json
{ "id": 1, "name": "Project A", "description": "Desc", "status": "archived", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions (editor or higher required), 404 — project not found, 409 — project name already exists

---

#### DELETE /projects/{project_id}

**Description:** Delete a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| N/A | N/A | N/A |

**Example request:**
```http
DELETE /projects/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```
HTTP/1.1 204 No Content
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions (owner required), 404 — project not found

---

### Sources Endpoints

#### GET /projects/{project_id}/sources

**Description:** List all sources for a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Source ID |
| project_id | integer | Parent project ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type: API, DB, FILE, STREAM |
| row_count | integer | Number of rows |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /projects/1/sources HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "project_id": 1, "name": "Source A", "description": "Desc", "type": "DB", "row_count": 1000, "last_updated": "2024-01-01T00:00:00Z", "created_at": "2024-01-01T00:00:00Z" }
]
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### GET /projects/{project_id}/sources/{source_id}

**Description:** Get a specific source by ID.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| source_id | path | integer | Yes | Source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Source ID |
| project_id | integer | Parent project ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | integer | Number of rows |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |
| mapping_table | object | Related mapping table (if any) |

**Example request:**
```http
GET /projects/1/sources/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "id": 1, "project_id": 1, "name": "Source A", "description": "Desc", "type": "DB", "row_count": 1000, "last_updated": "2024-01-01T00:00:00Z", "created_at": "2024-01-01T00:00:00Z", "mapping_table": null }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — source not found

---

#### POST /projects/{project_id}/sources

**Description:** Create a new source for a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| name | body | string | Yes | Source name |
| description | body | string | No | Source description |
| type | body | string | Yes | Source type: API, DB, FILE, STREAM |
| row_count | body | integer | No | Number of rows (default: 0) |
| mapping_table_id | body | integer | No | Related mapping table ID |
| last_updated | body | datetime | No | Last update timestamp |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Source ID |
| project_id | integer | Parent project ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | integer | Number of rows |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
POST /projects/1/sources HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "name": "New Source", "type": "DB", "row_count": 0 }
```

**Example response:**
```json
{ "id": 2, "project_id": 1, "name": "New Source", "description": null, "type": "DB", "row_count": 0, "last_updated": null, "created_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### PATCH /projects/{project_id}/sources/{source_id}

**Description:** Update an existing source (partial update).

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| source_id | path | integer | Yes | Source ID |
| name | body | string | No | New source name |
| description | body | string | No | New source description |
| type | body | string | No | New source type |
| row_count | body | integer | No | New row count |
| mapping_table_id | body | integer | No | New mapping table ID |
| last_updated | body | datetime | No | New last update timestamp |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Source ID |
| project_id | integer | Parent project ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | integer | Number of rows |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
PATCH /projects/1/sources/1 HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "row_count": 2000 }
```

**Example response:**
```json
{ "id": 1, "project_id": 1, "name": "Source A", "description": "Desc", "type": "DB", "row_count": 2000, "last_updated": "2024-01-01T00:00:00Z", "created_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — source not found

---

#### DELETE /projects/{project_id}/sources/{source_id}

**Description:** Delete a source.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| source_id | path | integer | Yes | Source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| N/A | N/A | N/A |

**Example request:**
```http
DELETE /projects/1/sources/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```
HTTP/1.1 204 No Content
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — source not found

---

#### GET /projects/{project_id}/sources/{source_id}/mapping-tables

**Description:** Get mapping tables associated with a source.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| source_id | path | integer | Yes | Source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Mapping table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
GET /projects/1/sources/1/mapping-tables HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "name": "Table A", "description": "Desc", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z", "columns": [] }
]
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — source not found

---

#### POST /projects/{project_id}/sources/{source_id}/mapping-tables

**Description:** Create a mapping table associated with a source.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| source_id | path | integer | Yes | Source ID |
| name | body | string | Yes | Table name |
| description | body | string | No | Table description |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Mapping table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
POST /projects/1/sources/1/mapping-tables HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "name": "New Table", "description": "Desc" }
```

**Example response:**
```json
{ "id": 2, "name": "New Table", "description": "Desc", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z", "columns": [] }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — source not found

---

### Mapping Tables Endpoints

#### GET /projects/{project_id}/mapping-tables

**Description:** List all mapping tables for a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
GET /projects/1/mapping-tables HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "name": "Table A", "description": "Desc", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z", "columns": [] }
]
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### GET /projects/{project_id}/mapping-tables/{table_id}

**Description:** Get a specific mapping table by ID.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
GET /projects/1/mapping-tables/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "id": 1, "name": "Table A", "description": "Desc", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z", "columns": [] }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — table not found

---

#### POST /projects/{project_id}/mapping-tables

**Description:** Create a new mapping table for a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| name | body | string | Yes | Table name |
| description | body | string | No | Table description |
| source_id | body | integer | No | Associated source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
POST /projects/1/mapping-tables HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "name": "New Table", "description": "Desc" }
```

**Example response:**
```json
{ "id": 2, "name": "New Table", "description": "Desc", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z", "columns": [] }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found, 404 — source not found (if source_id provided)

---

#### PATCH /projects/{project_id}/mapping-tables/{table_id}

**Description:** Update an existing mapping table (partial update).

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |
| name | body | string | No | New table name |
| description | body | string | No | New table description |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Table ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| columns | array | List of columns |

**Example request:**
```http
PATCH /projects/1/mapping-tables/1 HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "description": "Updated description" }
```

**Example response:**
```json
{ "id": 1, "name": "Table A", "description": "Updated description", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z", "columns": [] }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — table not found

---

#### DELETE /projects/{project_id}/mapping-tables/{table_id}

**Description:** Delete a mapping table.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| N/A | N/A | N/A |

**Example request:**
```http
DELETE /projects/1/mapping-tables/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```
HTTP/1.1 204 No Content
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — table not found

---

#### GET /projects/{project_id}/mapping-tables/{table_id}/columns

**Description:** List all columns for a mapping table.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Column ID |
| mapping_table_id | integer | Parent table ID |
| name | string | Column name |
| type | string | Column type: dimension, metric |
| data_type | string | Data type (string, integer, float, boolean, date, datetime) |
| description | string | Column description |
| is_calculated | boolean | Whether column is calculated |
| formula | string | Formula for calculated columns |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /projects/1/mapping-tables/1/columns HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "mapping_table_id": 1, "name": "customer_id", "type": "dimension", "data_type": "integer", "description": "Customer ID", "is_calculated": false, "formula": null, "created_at": "2024-01-01T00:00:00Z" }
]
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — table not found

---

#### GET /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}

**Description:** Get a specific column by ID.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |
| column_id | path | integer | Yes | Column ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Column ID |
| mapping_table_id | integer | Parent table ID |
| name | string | Column name |
| type | string | Column type |
| data_type | string | Data type |
| description | string | Column description |
| is_calculated | boolean | Whether column is calculated |
| formula | string | Formula for calculated columns |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /projects/1/mapping-tables/1/columns/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "id": 1, "mapping_table_id": 1, "name": "customer_id", "type": "dimension", "data_type": "integer", "description": "Customer ID", "is_calculated": false, "formula": null, "created_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — column not found

---

#### POST /projects/{project_id}/mapping-tables/{table_id}/columns

**Description:** Create a new column for a mapping table.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |
| name | body | string | Yes | Column name |
| type | body | string | Yes | Column type: dimension, metric |
| data_type | body | string | Yes | Data type: string, integer, float, boolean, date, datetime |
| description | body | string | No | Column description |
| is_calculated | body | boolean | No | Whether column is calculated (default: false) |
| formula | body | string | No | Formula (required if is_calculated=true) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Column ID |
| mapping_table_id | integer | Parent table ID |
| name | string | Column name |
| type | string | Column type |
| data_type | string | Data type |
| description | string | Column description |
| is_calculated | boolean | Whether column is calculated |
| formula | string | Formula for calculated columns |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
POST /projects/1/mapping-tables/1/columns HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "name": "revenue", "type": "metric", "data_type": "float", "description": "Revenue", "is_calculated": false }
```

**Example response:**
```json
{ "id": 2, "mapping_table_id": 1, "name": "revenue", "type": "metric", "data_type": "float", "description": "Revenue", "is_calculated": false, "formula": null, "created_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — table not found, 422 — validation error (formula required for calculated columns)

---

#### PATCH /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}

**Description:** Update an existing column (partial update).

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |
| column_id | path | integer | Yes | Column ID |
| name | body | string | No | New column name |
| type | body | string | No | New column type |
| data_type | body | string | No | New data type |
| description | body | string | No | New description |
| is_calculated | body | boolean | No | New calculated flag |
| formula | body | string | No | New formula |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Column ID |
| mapping_table_id | integer | Parent table ID |
| name | string | Column name |
| type | string | Column type |
| data_type | string | Data type |
| description | string | Column description |
| is_calculated | boolean | Whether column is calculated |
| formula | string | Formula for calculated columns |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
PATCH /projects/1/mapping-tables/1/columns/1 HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "description": "Updated description" }
```

**Example response:**
```json
{ "id": 1, "mapping_table_id": 1, "name": "customer_id", "type": "dimension", "data_type": "integer", "description": "Updated description", "is_calculated": false, "formula": null, "created_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — column not found, 422 — validation error

---

#### DELETE /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}

**Description:** Delete a column.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| table_id | path | integer | Yes | Table ID |
| column_id | path | integer | Yes | Column ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| N/A | N/A | N/A |

**Example request:**
```http
DELETE /projects/1/mapping-tables/1/columns/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```
HTTP/1.1 204 No Content
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — column not found

---

### RPI Mappings Endpoints

#### GET /projects/{project_id}/rpi-mappings/stats

**Description:** Get statistics for RPI mappings in a project.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| total | integer | Total number of RPI mappings |
| approved | integer | Number of approved mappings |
| in_review | integer | Number of in-review mappings |
| draft | integer | Number of draft mappings |

**Example request:**
```http
GET /projects/1/rpi-mappings/stats HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "total": 50, "approved": 20, "in_review": 10, "draft": 20 }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### GET /projects/{project_id}/rpi-mappings

**Description:** List RPI mappings with filtering and pagination.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| status | query | string | No | Filter by status: approved, in_review, draft |
| ownership | query | string | No | Filter by ownership |
| measurement_type | query | string | No | Filter by type: dimension, metric |
| is_calculated | query | boolean | No | Filter by calculated flag |
| search | query | string | No | Search in measurement, object_field, ownership |
| skip | query | integer | No | Pagination offset (default: 0) |
| limit | query | integer | No | Page size (default: 20, max: 100) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | RPI mapping ID |
| number | integer | RPI number |
| project_id | integer | Parent project ID |
| ownership | string | Ownership |
| status | string | Status |
| block | string | Block |
| measurement_type | string | Measurement type |
| is_calculated | boolean | Whether calculated |
| formula | string | Formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report |
| object_field | string | Object field |
| source_column_id | integer | Source column ID |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/1/rpi-mappings?status=approved&limit=10 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
[
  { "id": 1, "number": 1, "project_id": 1, "ownership": "Finance", "status": "approved", "block": "Block 1", "measurement_type": "metric", "is_calculated": false, "formula": null, "measurement": "Revenue", "measurement_description": "Total revenue", "source_report": "Report 1", "object_field": "revenue", "source_column_id": null, "date_added": "2024-01-01", "date_removed": null, "comment": "Approved", "verification_file": null, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
]
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found

---

#### GET /projects/{project_id}/rpi-mappings/{rpi_id}

**Description:** Get a specific RPI mapping by ID.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| rpi_id | path | integer | Yes | RPI mapping ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | RPI mapping ID |
| number | integer | RPI number |
| project_id | integer | Parent project ID |
| ownership | string | Ownership |
| status | string | Status |
| block | string | Block |
| measurement_type | string | Measurement type |
| is_calculated | boolean | Whether calculated |
| formula | string | Formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report |
| object_field | string | Object field |
| source_column_id | integer | Source column ID |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/1/rpi-mappings/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```json
{ "id": 1, "number": 1, "project_id": 1, "ownership": "Finance", "status": "approved", "block": "Block 1", "measurement_type": "metric", "is_calculated": false, "formula": null, "measurement": "Revenue", "measurement_description": "Total revenue", "source_report": "Report 1", "object_field": "revenue", "source_column_id": null, "date_added": "2024-01-01", "date_removed": null, "comment": "Approved", "verification_file": null, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — RPI mapping not found

---

#### POST /projects/{project_id}/rpi-mappings

**Description:** Create a new RPI mapping.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| number | body | integer | No | RPI number (auto-incremented if not provided) |
| ownership | body | string | No | Ownership |
| status | body | string | No | Status: approved, in_review, draft (default: draft) |
| block | body | string | No | Block |
| measurement_type | body | string | Yes | Measurement type: dimension, metric |
| is_calculated | body | boolean | No | Whether calculated (default: false) |
| formula | body | string | No | Formula (required if is_calculated=true) |
| measurement | body | string | Yes | Measurement name |
| measurement_description | body | string | No | Measurement description |
| source_report | body | string | No | Source report |
| object_field | body | string | Yes | Object field |
| source_column_id | body | integer | No | Source column ID |
| date_added | body | date | No | Date added |
| date_removed | body | date | No | Date removed |
| comment | body | string | No | Comment |
| verification_file | body | string | No | Verification file |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | RPI mapping ID |
| number | integer | RPI number |
| project_id | integer | Parent project ID |
| ownership | string | Ownership |
| status | string | Status |
| block | string | Block |
| measurement_type | string | Measurement type |
| is_calculated | boolean | Whether calculated |
| formula | string | Formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report |
| object_field | string | Object field |
| source_column_id | integer | Source column ID |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /projects/1/rpi-mappings HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "ownership": "Finance", "status": "draft", "block": "Block 1", "measurement_type": "metric", "measurement": "Revenue", "object_field": "revenue" }
```

**Example response:**
```json
{ "id": 1, "number": 1, "project_id": 1, "ownership": "Finance", "status": "draft", "block": "Block 1", "measurement_type": "metric", "is_calculated": false, "formula": null, "measurement": "Revenue", "measurement_description": null, "source_report": null, "object_field": "revenue", "source_column_id": null, "date_added": null, "date_removed": null, "comment": null, "verification_file": null, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found, 404 — source column not found (if source_column_id provided), 422 — validation error

---

#### PATCH /projects/{project_id}/rpi-mappings/{rpi_id}

**Description:** Update an existing RPI mapping (partial update).

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| rpi_id | path | integer | Yes | RPI mapping ID |
| ownership | body | string | No | New ownership |
| status | body | string | No | New status |
| block | body | string | No | New block |
| measurement_type | body | string | No | New measurement type |
| is_calculated | body | boolean | No | New calculated flag |
| formula | body | string | No | New formula |
| measurement | body | string | No | New measurement name |
| measurement_description | body | string | No | New description |
| source_report | body | string | No | New source report |
| object_field | body | string | No | New object field |
| source_column_id | body | integer | No | New source column ID |
| date_added | body | date | No | New date added |
| date_removed | body | date | No | New date removed |
| comment | body | string | No | New comment |
| verification_file | body | string | No | New verification file |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | integer | RPI mapping ID |
| number | integer | RPI number |
| project_id | integer | Parent project ID |
| ownership | string | Ownership |
| status | string | Status |
| block | string | Block |
| measurement_type | string | Measurement type |
| is_calculated | boolean | Whether calculated |
| formula | string | Formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report |
| object_field | string | Object field |
| source_column_id | integer | Source column ID |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PATCH /projects/1/rpi-mappings/1 HTTP/1.1
Content-Type: application/json
Authorization: Bearer ...

{ "status": "in_review" }
```

**Example response:**
```json
{ "id": 1, "number": 1, "project_id": 1, "ownership": "Finance", "status": "in_review", "block": "Block 1", "measurement_type": "metric", "is_calculated": false, "formula": null, "measurement": "Revenue", "measurement_description": "Total revenue", "source_report": "Report 1", "object_field": "revenue", "source_column_id": null, "date_added": "2024-01-01", "date_removed": null, "comment": "In review", "verification_file": null, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-02T00:00:00Z" }
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — RPI mapping not found

---

#### DELETE /projects/{project_id}/rpi-mappings/{rpi_id}

**Description:** Delete an RPI mapping.

**Auth required:** Yes

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | integer | Yes | Project ID |
| rpi_id | path | integer | Yes | RPI mapping ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| N/A | N/A | N/A |

**Example request:**
```http
DELETE /projects/1/rpi-mappings/1 HTTP/1.1
Authorization: Bearer ...
```

**Example response:**
```
HTTP/1.1 204 No Content
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — RPI mapping not found

---

### Health Check Endpoint

#### GET /health

**Description:** Health check endpoint to verify service availability.

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| N/A | N/A | N/A | N/A | N/A |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| status | string | Service status ("healthy") |
| redis | boolean | Redis connection status |

**Example request:**
```http
GET /health HTTP/1.1
```

**Example response:**
```json
{ "status": "healthy", "redis": true }
```

**Error codes:** None

---

## 5. Data Models & Schemas

### Database Models

#### User Model

**Table:** `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | User ID |
| email | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | User email address |
| full_name | VARCHAR(255) | NULL | User's full name |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt-hashed password |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether user is active |
| is_superuser | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether user is superuser |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Relationships:**
- One-to-many: `User` → `ProjectMember` (via `project_memberships`)

---

#### Project Model

**Table:** `projects`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Project ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Project name |
| description | TEXT | NULL | Project description |
| status | ENUM | NOT NULL, DEFAULT 'draft' | Project status: active, draft, archived |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Relationships:**
- One-to-many: `Project` → `Source`
- One-to-many: `Project` → `MappingTable`
- One-to-many: `Project` → `RPIMapping`
- One-to-many: `Project` → `ProjectMember`

---

#### ProjectMember Model

**Table:** `project_members`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Membership ID |
| user_id | INTEGER | NOT NULL, FOREIGN KEY → users.id, INDEX | User ID |
| project_id | INTEGER | NOT NULL, FOREIGN KEY → projects.id, INDEX | Project ID |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'viewer' | Role: owner, editor, viewer |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Constraints:**
- UNIQUE(user_id, project_id) — prevents duplicate memberships

**Relationships:**
- Many-to-one: `ProjectMember` → `User` (via `user`)
- Many-to-one: `ProjectMember` → `Project` (via `project`)

---

#### Source Model

**Table:** `sources`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Source ID |
| project_id | INTEGER | NOT NULL, FOREIGN KEY → projects.id, ON DELETE CASCADE | Parent project ID |
| mapping_table_id | INTEGER | NULL, FOREIGN KEY → mapping_tables.id, ON DELETE SET NULL | Associated mapping table ID |
| name | VARCHAR(255) | NOT NULL | Source name |
| description | TEXT | NULL | Source description |
| type | ENUM | NOT NULL, DEFAULT 'DB' | Source type: API, DB, FILE, STREAM |
| row_count | BIGINT | NOT NULL, DEFAULT 0 | Number of rows |
| last_updated | TIMESTAMP WITH TIME ZONE | NULL | Last update timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Relationships:**
- Many-to-one: `Source` → `Project` (via `project`)
- Many-to-one: `Source` → `MappingTable` (via `mapping_table`)

---

#### MappingTable Model

**Table:** `mapping_tables`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Table ID |
| project_id | INTEGER | NOT NULL, FOREIGN KEY → projects.id, ON DELETE CASCADE | Parent project ID |
| name | VARCHAR(255) | NOT NULL | Table name |
| description | TEXT | NULL | Table description |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Relationships:**
- Many-to-one: `MappingTable` → `Project` (via `project`)
- One-to-many: `MappingTable` → `MappingColumn`
- One-to-many: `MappingTable` → `Source` (via `sources.mapping_table_id`)

---

#### MappingColumn Model

**Table:** `mapping_columns`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Column ID |
| mapping_table_id | INTEGER | NOT NULL, FOREIGN KEY → mapping_tables.id, ON DELETE CASCADE | Parent table ID |
| name | VARCHAR(255) | NOT NULL | Column name |
| type | ENUM | NOT NULL, DEFAULT 'dimension' | Column type: dimension, metric |
| data_type | VARCHAR(64) | NOT NULL | Data type: string, integer, float, boolean, date, datetime |
| description | TEXT | NULL | Column description |
| is_calculated | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether column is calculated |
| formula | TEXT | NULL | Formula for calculated columns |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Relationships:**
- Many-to-one: `MappingColumn` → `MappingTable` (via `mapping_table`)
- One-to-many: `MappingColumn` → `RPIMapping` (via `rpi_mappings`)

---

#### RPIMapping Model

**Table:** `rpi_mappings`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | RPI mapping ID |
| number | INTEGER | NULL | RPI number (auto-incremented) |
| project_id | INTEGER | NOT NULL, FOREIGN KEY → projects.id, ON DELETE CASCADE | Parent project ID |
| source_column_id | INTEGER | NULL, FOREIGN KEY → mapping_columns.id, ON DELETE SET NULL | Source column ID |
| ownership | VARCHAR(128) | NULL | Ownership |
| status | ENUM | NOT NULL, DEFAULT 'draft' | Status: approved, in_review, draft |
| block | VARCHAR(128) | NULL | Block |
| measurement_type | ENUM | NOT NULL | Measurement type: dimension, metric |
| is_calculated | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether calculated |
| formula | TEXT | NULL | Formula for calculated columns |
| measurement | VARCHAR(255) | NOT NULL | Measurement name |
| measurement_description | TEXT | NULL | Measurement description |
| source_report | VARCHAR(255) | NULL | Source report |
| object_field | VARCHAR(255) | NOT NULL | Object field |
| date_added | DATE | NULL | Date added |
| date_removed | DATE | NULL | Date removed |
| comment | TEXT | NULL | Comment |
| verification_file | VARCHAR(512) | NULL | Verification file |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Constraints:**
- CHECK: `(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)` — ensures formula is provided for calculated columns

**Relationships:**
- Many-to-one: `RPIMapping` → `Project` (via `project`)
- Many-to-one: `RPIMapping` → `MappingColumn` (via `source_column`)

---

### ER Diagram

```mermaid
erDiagram
    USERS ||--o{ PROJECT_MEMBERS : "has membership"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has members"
    PROJECTS ||--o{ SOURCES : "has sources"
    PROJECTS ||--o{ MAPPING_TABLES : "has tables"
    PROJECTS ||--o{ RPI_MAPPINGS : "has mappings"
    MAPPING_TABLES ||--o{ MAPPING_COLUMNS : "has columns"
    MAPPING_TABLES ||--o{ SOURCES : "is mapped by"
    MAPPING_COLUMNS ||--o{ RPI_MAPPINGS : "is source for"
```

---

### Pydantic Schemas

#### User Schemas

**[`UserBase`](app/schemas/user.py:11):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | EmailStr | Yes | User email address |
| full_name | str \| None | No | User's full name |

**[`UserCreate`](app/schemas/user.py:20):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | EmailStr | Yes | User email address |
| full_name | str \| None | No | User's full name |
| password | str | Yes | Password (min 8 characters) |

**[`UserUpdate`](app/schemas/user.py:28):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | EmailStr \| None | No | New email |
| full_name | str \| None | No | New full name |
| password | str \| None | No | New password (min 8 characters) |
| is_active | bool \| None | No | New active status |
| is_superuser | bool \| None | No | New superuser status |

**[`UserOut`](app/schemas/user.py:44):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | User ID |
| email | EmailStr | Yes | User email |
| full_name | str \| None | No | User's full name |
| is_active | bool | Yes | Whether active |
| is_superuser | bool | Yes | Whether superuser |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**[`UserLogin`](app/schemas/user.py:59):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | str | Yes | User email |
| password | str | Yes | Password |

**[`Token`](app/schemas/user.py:68):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| access_token | str | Yes | JWT token |
| token_type | Literal["bearer"] | Yes | Token type (always "bearer") |

---

#### Project Schemas

**[`ProjectBase`](app/schemas/project.py:8):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Project name (max 255 chars) |
| description | str \| None | No | Project description |
| status | ProjectStatus | No | Status: active, draft, archived (default: draft) |

**[`ProjectCreate`](app/schemas/project.py:18):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Project name |
| description | str \| None | No | Project description |
| status | ProjectStatus | No | Status (default: draft) |

**[`ProjectUpdate`](app/schemas/project.py:26):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str \| None | No | New name |
| description | str \| None | No | New description |
| status | ProjectStatus \| None | No | New status |

**[`ProjectOut`](app/schemas/project.py:38):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Project ID |
| name | str | Yes | Project name |
| description | str \| None | No | Project description |
| status | ProjectStatus | Yes | Project status |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**[`ProjectKPIOut`](app/schemas/project.py:50):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total | int | Yes | Total projects |
| active | int | Yes | Active projects |
| draft | int | Yes | Draft projects |
| archived | int | Yes | Archived projects |

**[`ProjectSummaryOut`](app/schemas/project.py:67):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Project ID |
| name | str | Yes | Project name |
| status | ProjectStatus | Yes | Project status |
| updated_at | datetime | Yes | Last update timestamp |

---

#### Source Schemas

**[`SourceBase`](app/schemas/source.py:27):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Source name |
| description | str \| None | No | Source description |
| type | SourceType | No | Type: API, DB, FILE, STREAM (default: DB) |
| row_count | int | No | Row count (default: 0) |
| mapping_table_id | int \| None | No | Mapping table ID |
| last_updated | datetime \| None | No | Last update timestamp |

**[`SourceCreate`](app/schemas/source.py:43):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Source name |
| description | str \| None | No | Source description |
| type | SourceType | Yes | Source type |
| row_count | int | No | Row count (default: 0) |
| mapping_table_id | int \| None | No | Mapping table ID |
| last_updated | datetime \| None | No | Last update timestamp |

**[`SourceUpdate`](app/schemas/source.py:47):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str \| None | No | New name |
| description | str \| None | No | New description |
| type | SourceType \| None | No | New type |
| row_count | int \| None | No | New row count |
| mapping_table_id | int \| None | No | New mapping table ID |
| last_updated | datetime \| None | No | New last update timestamp |

**[`SourceOut`](app/schemas/source.py:56):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Source ID |
| project_id | int | Yes | Parent project ID |
| name | str | Yes | Source name |
| description | str \| None | No | Source description |
| type | SourceType | Yes | Source type |
| row_count | int | Yes | Row count |
| last_updated | datetime \| None | No | Last update timestamp |
| created_at | datetime | Yes | Creation timestamp |

**[`SourceDetailOut`](app/schemas/source.py:11):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Source ID |
| project_id | int | Yes | Parent project ID |
| name | str | Yes | Source name |
| description | str \| None | No | Source description |
| type | SourceType | Yes | Source type |
| row_count | int | Yes | Row count |
| last_updated | datetime \| None | No | Last update timestamp |
| created_at | datetime | Yes | Creation timestamp |
| mapping_table | MappingTableOut \| None | No | Related mapping table |

---

#### Mapping Table Schemas

**[`MappingColumnBase`](app/schemas/mapping_table.py:19):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Column name |
| type | ColumnType | No | Type: dimension, metric (default: dimension) |
| data_type | str | Yes | Data type |
| description | str \| None | No | Column description |
| is_calculated | bool | No | Whether calculated (default: false) |
| formula | str \| None | No | Formula (required if is_calculated=true) |

**[`MappingColumnCreate`](app/schemas/mapping_table.py:36):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Column name |
| type | ColumnType | No | Type (default: dimension) |
| data_type | DataType | Yes | Data type: string, integer, float, boolean, date, datetime |
| description | str \| None | No | Column description |
| is_calculated | bool | No | Whether calculated (default: false) |
| formula | str \| None | No | Formula |

**[`MappingColumnUpdate`](app/schemas/mapping_table.py:40):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str \| None | No | New name |
| type | ColumnType \| None | No | New type |
| data_type | str \| None | No | New data type |
| description | str \| None | No | New description |
| is_calculated | bool \| None | No | New calculated flag |
| formula | str \| None | No | New formula |

**[`MappingColumnOut`](app/schemas/mapping_table.py:49):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Column ID |
| mapping_table_id | int | Yes | Parent table ID |
| name | str | Yes | Column name |
| type | ColumnType | Yes | Column type |
| data_type | str | Yes | Data type |
| description | str \| None | No | Column description |
| is_calculated | bool | Yes | Whether calculated |
| formula | str \| None | No | Formula |
| created_at | datetime | Yes | Creation timestamp |

**[`MappingTableBase`](app/schemas/mapping_table.py:58):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Table name |
| description | str \| None | No | Table description |

**[`MappingTableCreate`](app/schemas/mapping_table.py:63):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Table name |
| description | str \| None | No | Table description |
| source_id | int \| None | No | Associated source ID |

**[`MappingTableUpdate`](app/schemas/mapping_table.py:67):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str \| None | No | New name |
| description | str \| None | No | New description |

**[`MappingTableOut`](app/schemas/mapping_table.py:72):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Table ID |
| name | str | Yes | Table name |
| description | str \| None | No | Table description |
| project_id | int | Yes | Parent project ID |
| source_id | int \| None | No | Associated source ID |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |
| columns | list[MappingColumnOut] | No | List of columns |

---

#### RPI Mapping Schemas

**[`RPIMappingBase`](app/schemas/rpi_mapping.py:44):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ownership | str \| None | No | Ownership |
| status | RPIStatus | No | Status: approved, in_review, draft (default: draft) |
| block | str \| None | No | Block |
| measurement_type | MeasurementType | Yes | Measurement type: dimension, metric |
| is_calculated | bool | No | Whether calculated (default: false) |
| formula | str \| None | No | Formula (required if is_calculated=true) |
| measurement | str | Yes | Measurement name |
| measurement_description | str \| None | No | Measurement description |
| source_report | str \| None | No | Source report |
| object_field | str | Yes | Object field |
| source_column_id | int \| None | No | Source column ID |
| date_added | date \| None | No | Date added |
| date_removed | date \| None | No | Date removed |
| comment | str \| None | No | Comment |
| verification_file | str \| None | No | Verification file |

**[`RPIMappingCreate`](app/schemas/rpi_mapping.py:68):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ownership | str \| None | No | Ownership |
| status | RPIStatus | No | Status (default: draft) |
| block | str \| None | No | Block |
| measurement_type | MeasurementType | Yes | Measurement type |
| is_calculated | bool | No | Whether calculated (default: false) |
| formula | str \| None | No | Formula |
| measurement | str | Yes | Measurement name |
| measurement_description | str \| None | No | Measurement description |
| source_report | str \| None | No | Source report |
| object_field | str | Yes | Object field |
| source_column_id | int \| None | No | Source column ID |
| date_added | date \| None | No | Date added |
| date_removed | date \| None | No | Date removed |
| comment | str \| None | No | Comment |
| verification_file | str \| None | No | Verification file |

**[`RPIMappingUpdate`](app/schemas/rpi_mapping.py:72):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| measurement | str \| None | No | New measurement name |
| object_field | str \| None | No | New object field |
| measurement_type | MeasurementType \| None | No | New measurement type |

**[`RPIMappingOut`](app/schemas/rpi_mapping.py:78):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | RPI mapping ID |
| number | int \| None | No | RPI number |
| project_id | int | Yes | Parent project ID |
| ownership | str \| None | No | Ownership |
| status | RPIStatus | Yes | Status |
| block | str \| None | No | Block |
| measurement_type | MeasurementType | Yes | Measurement type |
| is_calculated | bool | Yes | Whether calculated |
| formula | str \| None | No | Formula |
| measurement | str | Yes | Measurement name |
| measurement_description | str \| None | No | Measurement description |
| source_report | str \| None | No | Source report |
| object_field | str | Yes | Object field |
| source_column_id | int \| None | No | Source column ID |
| date_added | date \| None | No | Date added |
| date_removed | date \| None | No | Date removed |
| comment | str \| None | No | Comment |
| verification_file | str \| None | No | Verification file |
| created_at | datetime | Yes | Creation timestamp |
| updated_at | datetime | Yes | Last update timestamp |

**[`RPIStatsOut`](app/schemas/rpi_mapping.py:89):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total | int | Yes | Total RPI mappings |
| approved | int | Yes | Approved mappings |
| in_review | int | Yes | In-review mappings |
| draft | int | Yes | Draft mappings |

---

## 6. Business Logic & Core Functions

### Service Layer Functions

#### Projects Service ([`app/services/projects.py`](app/services/projects.py:1))

**[`get_list(db)`](app/services/projects.py:32):**
- **Purpose:** Retrieve all projects with Redis caching
- **Parameters:** `db: AsyncSession`
- **Returns:** `list[Project]`
- **Side effects:** Reads from cache or DB, writes to cache if miss
- **Usage:** Called by `GET /projects` endpoint

**[`get_one(db, project_id)`](app/services/projects.py:73):**
- **Purpose:** Get a single project by ID with caching
- **Parameters:** `db: AsyncSession`, `project_id: int`
- **Returns:** `Project \| None`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}` endpoint

**[`get_kpi(db)`](app/services/projects.py:111):**
- **Purpose:** Calculate aggregated KPI statistics
- **Parameters:** `db: AsyncSession`
- **Returns:** `ProjectKPIOut`
- **Side effects:** Cache read/write, DB aggregation query
- **Usage:** Called by `GET /projects/kpi` endpoint

**[`get_recent(db, user_id, limit)`](app/services/projects.py:138):**
- **Purpose:** Get recently updated projects
- **Parameters:** `db: AsyncSession`, `user_id: int \| None`, `limit: int`
- **Returns:** `list[Project]`
- **Side effects:** Cache read/write for default limit=5
- **Usage:** Called by `GET /projects/recent` endpoint

**[`create(db, payload, user_id)`](app/services/projects.py:180):**
- **Purpose:** Create a new project and add user as owner
- **Parameters:** `db: AsyncSession`, `payload: ProjectCreate`, `user_id: int`
- **Returns:** `Project`
- **Side effects:** DB INSERT, creates ProjectMember, invalidates caches
- **Usage:** Called by `POST /projects` endpoint

**[`update(db, project_id, payload)`](app/services/projects.py:230):**
- **Purpose:** Update an existing project
- **Parameters:** `db: AsyncSession`, `project_id: int`, `payload: ProjectUpdate`
- **Returns:** `Project \| None`
- **Side effects:** DB UPDATE, invalidates caches
- **Usage:** Called by `PATCH /projects/{project_id}` endpoint

**[`delete(db, project_id)`](app/services/projects.py:282):**
- **Purpose:** Delete a project
- **Parameters:** `db: AsyncSession`, `project_id: int`
- **Returns:** `bool`
- **Side effects:** DB DELETE, invalidates caches
- **Usage:** Called by `DELETE /projects/{project_id}` endpoint

**[`get_filtered_list(db, status, search, page, size, sort_by, sort_dir)`](app/services/projects.py:318):**
- **Purpose:** Get filtered and paginated project list
- **Parameters:** `db: AsyncSession`, `status: ProjectStatus \| None`, `search: str \| None`, `page: int`, `size: int`, `sort_by: str`, `sort_dir: str`
- **Returns:** `list[Project]`
- **Side effects:** DB query with filters
- **Usage:** Called by `GET /projects` with query parameters

**[`check_owner_access(db, project_id, user_id)`](app/services/projects.py:367):**
- **Purpose:** Check if user is project owner
- **Parameters:** `db: AsyncSession`, `project_id: int`, `user_id: int`
- **Returns:** `bool`
- **Side effects:** DB query
- **Usage:** Authorization check for delete operations

**[`check_editor_access(db, project_id, user_id)`](app/services/projects.py:389):**
- **Purpose:** Check if user has editor or owner role
- **Parameters:** `db: AsyncSession`, `project_id: int`, `user_id: int`
- **Returns:** `bool`
- **Side effects:** DB query
- **Usage:** Authorization check for update operations

**[`check_viewer_access(db, project_id, user_id)`](app/services/projects.py:411):**
- **Purpose:** Check if user has any access to project
- **Parameters:** `db: AsyncSession`, `project_id: int`, `user_id: int`
- **Returns:** `bool`
- **Side effects:** DB query
- **Usage:** Authorization check for read operations

---

#### Sources Service ([`app/services/sources.py`](app/services/sources.py:1))

**[`get_list(db, project_id)`](app/services/sources.py:10):**
- **Purpose:** Get all sources for a project
- **Parameters:** `db: AsyncSession`, `project_id: int`
- **Returns:** `list[Source]`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}/sources`

**[`get_one(db, project_id, source_id)`](app/services/sources.py:32):**
- **Purpose:** Get a single source with mapping table
- **Parameters:** `db: AsyncSession`, `project_id: int`, `source_id: int`
- **Returns:** `Source \| None`
- **Side effects:** Cache read/write, DB query with selectinload
- **Usage:** Called by `GET /projects/{project_id}/sources/{source_id}`

**[`create(db, project_id, payload)`](app/services/sources.py:54):**
- **Purpose:** Create a new source
- **Parameters:** `db: AsyncSession`, `project_id: int`, `payload: SourceCreate`
- **Returns:** `Source`
- **Side effects:** DB INSERT, cache invalidation
- **Usage:** Called by `POST /projects/{project_id}/sources`

**[`update(db, project_id, source_id, payload)`](app/services/sources.py:63):**
- **Purpose:** Update an existing source
- **Parameters:** `db: AsyncSession`, `project_id: int`, `source_id: int`, `payload: SourceUpdate`
- **Returns:** `Source \| None`
- **Side effects:** DB UPDATE, cache invalidation
- **Usage:** Called by `PATCH /projects/{project_id}/sources/{source_id}`

**[`delete(db, project_id, source_id)`](app/services/sources.py:89):**
- **Purpose:** Delete a source
- **Parameters:** `db: AsyncSession`, `project_id: int`, `source_id: int`
- **Returns:** `bool`
- **Side effects:** DB DELETE, cache invalidation
- **Usage:** Called by `DELETE /projects/{project_id}/sources/{source_id}`

---

#### Mapping Tables Service ([`app/services/mapping_tables.py`](app/services/mapping_tables.py:1))

**[`get_list(db, project_id)`](app/services/mapping_tables.py:28):**
- **Purpose:** Get all mapping tables with columns
- **Parameters:** `db: AsyncSession`, `project_id: int`
- **Returns:** `list[MappingTableOut]`
- **Side effects:** Cache read/write, DB query with joins
- **Usage:** Called by `GET /projects/{project_id}/mapping-tables`

**[`get_one(db, project_id, table_id)`](app/services/mapping_tables.py:70):**
- **Purpose:** Get a single mapping table with columns
- **Parameters:** `db: AsyncSession`, `project_id: int`, `table_id: int`
- **Returns:** `MappingTableOut \| None`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}/mapping-tables/{table_id}`

**[`create(db, project_id, payload)`](app/services/mapping_tables.py:101):**
- **Purpose:** Create a new mapping table
- **Parameters:** `db: AsyncSession`, `project_id: int`, `payload: MappingTableCreate`
- **Returns:** `MappingTableOut`
- **Side effects:** DB INSERT, updates source.mapping_table_id, cache invalidation
- **Usage:** Called by `POST /projects/{project_id}/mapping-tables`

**[`update(db, project_id, table_id, payload)`](app/services/mapping_tables.py:144):**
- **Purpose:** Update a mapping table
- **Parameters:** `db: AsyncSession`, `project_id: int`, `table_id: int`, `payload: MappingTableUpdate`
- **Returns:** `MappingTableOut \| None`
- **Side effects:** DB UPDATE, updates source.mapping_table_id if changed, cache invalidation
- **Usage:** Called by `PATCH /projects/{project_id}/mapping-tables/{table_id}`

**[`delete(db, project_id, table_id)`](app/services/mapping_tables.py:206):**
- **Purpose:** Delete a mapping table
- **Parameters:** `db: AsyncSession`, `project_id: int`, `table_id: int`
- **Returns:** `bool`
- **Side effects:** DB DELETE, cache invalidation
- **Usage:** Called by `DELETE /projects/{project_id}/mapping-tables/{table_id}`

**[`get_by_source(db, project_id, source_id)`](app/services/mapping_tables.py:228):**
- **Purpose:** Get mapping tables associated with a source
- **Parameters:** `db: AsyncSession`, `project_id: int`, `source_id: int`
- **Returns:** `list[MappingTableOut]`
- **Side effects:** DB query
- **Usage:** Called by `GET /projects/{project_id}/sources/{source_id}/mapping-tables`

**[`get_columns(db, table_id)`](app/services/mapping_tables.py:268):**
- **Purpose:** Get all columns for a table
- **Parameters:** `db: AsyncSession`, `table_id: int`
- **Returns:** `list[MappingColumnOut]`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}/mapping-tables/{table_id}/columns`

**[`get_column(db, table_id, column_id)`](app/services/mapping_tables.py:291):**
- **Purpose:** Get a single column
- **Parameters:** `db: AsyncSession`, `table_id: int`, `column_id: int`
- **Returns:** `MappingColumnOut \| None`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}`

**[`create_column(db, table_id, payload)`](app/services/mapping_tables.py:315):**
- **Purpose:** Create a new column
- **Parameters:** `db: AsyncSession`, `table_id: int`, `payload: MappingColumnCreate`
- **Returns:** `MappingColumnOut`
- **Side effects:** DB INSERT, cache invalidation
- **Usage:** Called by `POST /projects/{project_id}/mapping-tables/{table_id}/columns`

**[`update_column(db, table_id, column_id, payload)`](app/services/mapping_tables.py:326):**
- **Purpose:** Update a column with cross-field validation
- **Parameters:** `db: AsyncSession`, `table_id: int`, `column_id: int`, `payload: MappingColumnUpdate`
- **Returns:** `MappingColumnOut \| None`
- **Side effects:** DB UPDATE, validates formula required for calculated columns, cache invalidation
- **Usage:** Called by `PATCH /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}`

**[`delete_column(db, table_id, column_id)`](app/services/mapping_tables.py:370):**
- **Purpose:** Delete a column
- **Parameters:** `db: AsyncSession`, `table_id: int`, `column_id: int`
- **Returns:** `bool`
- **Side effects:** DB DELETE, cache invalidation
- **Usage:** Called by `DELETE /projects/{project_id}/mapping-tables/{table_id}/columns/{column_id}`

---

#### RPI Mappings Service ([`app/services/rpi_mappings.py`](app/services/rpi_mappings.py:1))

**[`get_list(db, project_id, status, ownership, measurement_type, is_calculated, search, skip, limit)`](app/services/rpi_mappings.py:27):**
- **Purpose:** Get RPI mappings with filters and pagination
- **Parameters:** `db: AsyncSession`, `project_id: int`, `status: str \| None`, `ownership: str \| None`, `measurement_type: str \| None`, `is_calculated: bool \| None`, `search: str \| None`, `skip: int`, `limit: int`
- **Returns:** `list[RPIMapping]`
- **Side effects:** Cache read/write with hash-based keys
- **Usage:** Called by `GET /projects/{project_id}/rpi-mappings`

**[`get_stats(db, project_id)`](app/services/rpi_mappings.py:84):**
- **Purpose:** Get RPI mapping statistics by status
- **Parameters:** `db: AsyncSession`, `project_id: int`
- **Returns:** `RPIStatsOut`
- **Side effects:** Cache read/write, DB aggregation
- **Usage:** Called by `GET /projects/{project_id}/rpi-mappings/stats`

**[`get_one(db, project_id, rpi_id)`](app/services/rpi_mappings.py:111):**
- **Purpose:** Get a single RPI mapping
- **Parameters:** `db: AsyncSession`, `project_id: int`, `rpi_id: int`
- **Returns:** `RPIMapping \| None`
- **Side effects:** Cache read/write
- **Usage:** Called by `GET /projects/{project_id}/rpi-mappings/{rpi_id}`

**[`create(db, project_id, payload)`](app/services/rpi_mappings.py:129):**
- **Purpose:** Create a new RPI mapping
- **Parameters:** `db: AsyncSession`, `project_id: int`, `payload: RPIMappingCreate`
- **Returns:** `RPIMapping`
- **Side effects:** DB INSERT, validates source_column_id, auto-increments number, cache invalidation
- **Usage:** Called by `POST /projects/{project_id}/rpi-mappings`

**[`update(db, project_id, rpi_id, payload)`](app/services/rpi_mappings.py:154):**
- **Purpose:** Update an RPI mapping
- **Parameters:** `db: AsyncSession`, `project_id: int`, `rpi_id: int`, `payload: RPIMappingUpdate`
- **Returns:** `RPIMapping \| None`
- **Side effects:** DB UPDATE, cache invalidation
- **Usage:** Called by `PATCH /projects/{project_id}/rpi-mappings/{rpi_id}`

**[`delete(db, project_id, rpi_id)`](app/services/rpi_mappings.py:178):**
- **Purpose:** Delete an RPI mapping
- **Parameters:** `db: AsyncSession`, `project_id: int`, `rpi_id: int`
- **Returns:** `bool`
- **Side effects:** DB DELETE, cache invalidation
- **Usage:** Called by `DELETE /projects/{project_id}/rpi-mappings/{rpi_id}`

---

#### Users Service ([`app/services/users.py`](app/services/users.py:1))

**[`get_one(db, user_id)`](app/services/users.py:13):**
- **Purpose:** Get a user by ID
- **Parameters:** `db: AsyncSession`, `user_id: int`
- **Returns:** `User \| None`
- **Side effects:** DB query
- **Usage:** Called by authentication and authorization

**[`get_by_email(db, email)`](app/services/users.py:28):**
- **Purpose:** Get a user by email
- **Parameters:** `db: AsyncSession`, `email: str`
- **Returns:** `User \| None`
- **Side effects:** DB query
- **Usage:** Called by login endpoints

**[`create(db, payload)`](app/services/users.py:43):**
- **Purpose:** Create a new user with hashed password
- **Parameters:** `db: AsyncSession`, `payload: UserCreate`
- **Returns:** `User`
- **Side effects:** DB INSERT, password hashing
- **Usage:** Called by `POST /auth/register`

**[`update(db, user_id, payload)`](app/services/users.py:68):**
- **Purpose:** Update a user
- **Parameters:** `db: AsyncSession`, `user_id: int`, `payload: UserUpdate`
- **Returns:** `User \| None`
- **Side effects:** DB UPDATE, password hashing if password changed
- **Usage:** Not currently exposed via API

**[`get_project_member(db, user_id, project_id)`](app/services/users.py:104):**
- **Purpose:** Get user's membership in a project
- **Parameters:** `db: AsyncSession`, `user_id: int`, `project_id: int`
- **Returns:** `ProjectMember \| None`
- **Side effects:** DB query
- **Usage:** Called by authorization dependencies

---

### Core Functions

#### Authentication ([`app/core/auth.py`](app/core/auth.py:1))

**[`get_current_user(db, token)`](app/core/auth.py:18):**
- **Purpose:** Extract and validate JWT token, return current user
- **Parameters:** `db: DBSession`, `token: str \| None`
- **Returns:** `User`
- **Side effects:** JWT verification, DB query
- **Usage:** Dependency for all authenticated endpoints

**[`get_current_active_superuser(current_user)`](app/core/auth.py:58):**
- **Purpose:** Ensure user is superuser
- **Parameters:** `current_user: CurrentUser`
- **Returns:** `User`
- **Side effects:** Role check
- **Usage:** Dependency for admin-only endpoints

**[`require_project_role(required_role)`](app/core/auth.py:79):**
- **Purpose:** Factory function for role-based project access
- **Parameters:** `required_role: ProjectRole`
- **Returns:** `dependency(project_id, db, current_user) -> Project`
- **Side effects:** Project lookup, membership check, role comparison
- **Usage:** Creates `ProjectViewer`, `ProjectEditor`, `ProjectOwner` dependencies

---

#### Cache ([`app/core/cache.py`](app/core/cache.py:1))

**[`cache_get(key)`](app/core/cache.py:42):**
- **Purpose:** Get value from Redis cache
- **Parameters:** `key: str`
- **Returns:** `Any \| None`
- **Side effects:** Redis GET, JSON deserialization
- **Usage:** All service layer cache reads

**[`cache_set(key, value, ttl)`](app/core/cache.py:47):**
- **Purpose:** Set value in Redis cache
- **Parameters:** `key: str`, `value: Any`, `ttl: int`
- **Returns:** `None`
- **Side effects:** Redis SET with TTL, JSON serialization
- **Usage:** All service layer cache writes

**[`cache_delete(*keys)`](app/core/cache.py:51):**
- **Purpose:** Delete one or more cache keys
- **Parameters:** `*keys: str`
- **Returns:** `None`
- **Side effects:** Redis DELETE
- **Usage:** Cache invalidation on writes

**[`cache_delete_pattern(pattern)`](app/core/cache.py:56):**
- **Purpose:** Delete all keys matching a pattern
- **Parameters:** `pattern: str`
- **Returns:** `None`
- **Side effects:** Redis SCAN + DELETE
- **Usage:** Bulk cache invalidation for project-specific keys

**[`project_key(project_id, suffix)`](app/core/cache.py:73):**
- **Purpose:** Generate cache key for a project
- **Parameters:** `project_id: int`, `suffix: str`
- **Returns:** `str`
- **Side effects:** None
- **Usage:** Key generation for project cache entries

**[`hash_params(**kwargs)`](app/core/cache.py:93):**
- **Purpose:** Generate hash from query parameters for cache key
- **Parameters:** `**kwargs`
- **Returns:** `str` (12-char MD5 prefix)
- **Side effects:** JSON serialization, MD5 hash
- **Usage:** Cache key generation for filtered list endpoints

---

#### Security ([`app/core/security.py`](app/core/security.py:1))

**[`get_password_hash(password)`](app/core/security.py:17):**
- **Purpose:** Hash password using bcrypt
- **Parameters:** `password: str`
- **Returns:** `str` (hashed password)
- **Side effects:** bcrypt hashing
- **Usage:** User registration, password update

**[`verify_password(plain, hashed)`](app/core/security.py:21):**
- **Purpose:** Verify password against hash
- **Parameters:** `plain: str`, `hashed: str`
- **Returns:** `bool`
- **Side effects:** bcrypt verification
- **Usage:** Login authentication

**[`create_access_token(data, expires_delta)`](app/core/security.py:28):**
- **Purpose:** Create JWT access token
- **Parameters:** `data: dict[str, Any]`, `expires_delta: timedelta \| None`
- **Returns:** `str` (JWT token)
- **Side effects:** JWT encoding with expiration
- **Usage:** Login response, token generation

**[`decode_token(token)`](app/core/security.py:45):**
- **Purpose:** Decode and verify JWT token
- **Parameters:** `token: str`
- **Returns:** `dict[str, Any] \| None`
- **Side effects:** JWT decoding, signature verification
- **Usage:** Authentication dependency

---

## 7. Configuration & Infrastructure

### Configuration Files

**[`app/core/config.py`](app/core/config.py:1):**
- Pydantic settings class loading from `.env` file
- Validates and provides type-safe access to all configuration
- Supports JSON parsing for CORS_ORIGINS

**[`pyproject.toml`](pyproject.toml:1):**
- Project metadata (name, version, description)
- Python version requirement (>=3.13)
- Dependencies specification
- pytest configuration (asyncio mode, test paths, timeout)
- Ruff linter and formatter configuration

**[`requirements.txt`](requirements.txt:1):**
- Minimal dependency list for production deployment
- Core packages: FastAPI, uvicorn, SQLAlchemy, asyncpg, Alembic, Pydantic, Redis

### Docker / Docker Compose

**[`docker-compose.yaml`](docker-compose.yaml:1):**

Services:
- **postgres:** PostgreSQL 16 Alpine
  - Ports: 5432:5432
  - Volumes: postgres_data
  - Health check: pg_isready
  - Environment: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (from .env)

- **redis:** Redis 7 Alpine
  - Ports: 6379:6379
  - Volumes: redis_data
  - Command: redis-server --save 60 1 --loglevel warning
  - Health check: redis-cli ping

Volumes:
- postgres_data: Persistent PostgreSQL data
- redis_data: Persistent Redis data

### CI/CD Pipeline

No CI/CD pipeline is currently configured in the repository. The `.github/` directory exists but contains no workflow files.

### Migrations Strategy

**Alembic Configuration:**
- Location: `alembic/`
- Script location: `alembic/versions/`
- Template: `script.py.mako`

**Migration History:**
1. `94aca1390145_init.py` — Initial schema creation
2. `35bc1c36160b_unique_proj_name.py` — Add unique constraint on project name
3. `4e3b3c8b6212_fix_source.py` — Source table fix
4. `965613165dd4_fix_mapping_table.py` — Mapping table fix
5. `ac218a78dc1f_fix_mapping_table_source_fk.py` — Fix foreign key on mapping_table_id
6. `f50fdec921f8_fix_circular_fk.py` — Resolve circular foreign key issue

**Migration Commands:**
```bash
# Generate new migration
alembic revision --autogenerate -m "Migration description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

---

## 8. Testing

### How to Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_projects_api.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with timeout
pytest --timeout=60

# Run tests with real Redis (skip mocked cache)
pytest -m use_real_redis
```

### Test Structure

**[`tests/conftest.py`](tests/conftest.py:1):**
- Session-scoped PostgreSQL engine and session factory
- Auto-cleanup fixture that truncates and reseeds tables
- Database override fixture for test isolation
- Redis mocking fixture (auto-mock unless `use_real_redis` marker)
- Authenticated client fixture
- Seeded project fixture for permission tests

**[`tests/factories.py`](tests/factories.py:1):**
- Async factory functions for test data creation:
  - `create_project()`
  - `create_source()`
  - `create_mapping_table()`
  - `create_mapping_column()`
  - `create_rpi()`

**Test Files:**
- `test_health.py` — Health check endpoint tests
- `test_contract.py` — API contract and schema validation tests
- `test_errors.py` — Error handling tests
- `test_functional_enhanced.py` — Comprehensive functional tests
- `test_integration.py` — Integration tests across components
- `test_mapping_tables_api.py` — Mapping tables API tests
- `test_performance_api.py` — Performance benchmark tests
- `test_projects_api.py` — Projects API tests
- `test_rpi_mappings_api.py` — RPI mappings API tests
- `test_security_api.py` — Security and authentication tests
- `test_sources_api.py` — Sources API tests
- `test_validation.py` — Input validation tests
- `test_cache.py` — Cache functionality tests

### Coverage Notes

The test suite provides comprehensive coverage:
- **Contract tests** ensure API response structure consistency
- **Functional tests** cover all CRUD operations
- **Integration tests** verify component interactions
- **Security tests** validate authentication and authorization
- **Performance tests** benchmark API response times

Test markers:
- `use_real_redis` — Run against real Redis instead of mocked cache

---

## 9. Known Limitations & TODOs

### Hard-coded Values

1. **[`app/core/config.py:18`](app/core/config.py:18):** Default JWT_SECRET_KEY is a placeholder — must be changed in production
2. **[`app/core/config.py:15`](app/core/config.py:15):** Default CORS_ORIGINS only allows localhost:5173
3. **[`app/services/projects.py:158`](app/services/projects.py:158):** TODO comment indicates ACL filtering for user_id is not yet implemented in `get_recent()`

### Known Bugs or Edge Cases

1. **[`app/routers/mapping_tables.py:123`](app/routers/mapping_tables.py:123):** `update_column` endpoint accepts `MappingColumnCreate` instead of `MappingColumnUpdate` — type mismatch
2. **[`app/services/mapping_tables.py:64`](app/services/mapping_tables.py:64):** `get_list` serializes using `RPIMappingOut` instead of `MappingTableOut` — likely a copy-paste error
3. **[`app/services/sources.py:47`](app/services/sources.py:47):** Debug `print(obj)` statement should be removed in production

### Planned Improvements (from code comments)

1. **[`app/services/projects.py:158-160`](app/services/projects.py:158):** Implement ACL filtering in `get_recent()` based on user permissions
2. **API versioning** — Currently not implemented (see `test_contract.py` comments)
3. **Deprecated endpoints warning** — Not implemented (see `test_contract.py` comments)
4. **API version negotiation** — Not implemented (see `test_contract.py` comments)

### Technical Debt

1. **Cache key inconsistency:** Some services use `__dict__` serialization, others use Pydantic `model_dump()`
2. **Return type inconsistency:** Some functions return ORM objects, others return Pydantic schemas
3. **Missing update endpoint:** User update functionality exists in service layer but is not exposed via API
4. **No soft delete:** All deletes are physical; soft delete would enable recovery

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **RPI** | Reporting and Planning Integration — the domain concept being modeled |
| **RPI Mapping** | A record linking a measurement to an object field, with ownership and status |
| **Mapping Table** | A structured definition of columns (dimensions and metrics) for data mapping |
| **Source** | A data source (API, DB, FILE, STREAM) that feeds into the mapping system |
| **Dimension** | A categorical attribute used for grouping/filtering in reports |
| **Metric** | A numerical measure to be aggregated in reports |
| **Calculated Column** | A column with a formula for computed values |
| **Bounded Context** | A domain modeling concept where each model has clear boundaries |
| **ACL** | Access Control List — role-based permissions (viewer, editor, owner) |
| **CQRS-lite** | Command Query Responsibility Segregation — separate read (cached) from write (DB) paths |
| **Cache-Aside** | Caching pattern where reads miss → load from DB → write to cache |
| **Alembic** | SQLAlchemy's database migration tool |
| **ORM** | Object-Relational Mapping — SQLAlchemy maps Python classes to database tables |
| **Pydantic** | Python data validation library using type hints |
| **JWT** | JSON Web Token — stateless authentication token |
| **ASGI** | Asynchronous Server Gateway Interface — FastAPI's server protocol |
| **AsyncSession** | SQLAlchemy's async session for non-blocking database operations |
| **Cascade** | Database referential action (CASCADE, SET NULL) for related records |
| **TTL** | Time-To-Live — cache expiration time in seconds |


