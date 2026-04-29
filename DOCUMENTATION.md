# LayerMap Back

> Backend API for RPI (Russian Performance Indicators) mapping and project management system.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-blue.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why This Exists

Organizations managing Russian Performance Indicators (RPI) need a centralized system to track, map, and validate metrics across multiple data sources. LayerMap provides a structured API for managing projects, connecting data sources (APIs, databases, files, streams), and mapping source columns to standardized RPI measurements with ownership tracking and calculation formulas.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/org/layermap-back.git
cd layermap-back

# Install dependencies
pip install -e .

# Start services with Docker
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

---

## 1. Project Overview

### Description

LayerMap Back is a Python/FastAPI backend service that provides RESTful API endpoints for managing RPI (Russian Performance Indicators) mapping projects. The system enables users to create projects, connect multiple data sources, define source tables and columns, and map them to standardized RPI measurements with ownership attribution and calculation formulas.

### Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Language** | Python | 3.13+ |
| **Web Framework** | FastAPI | 0.111.0+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Database Driver** | asyncpg | 0.29.0+ |
| **Database** | PostgreSQL | 16+ |
| **Migrations** | Alembic | 1.13.0+ |
| **Validation** | Pydantic | 2.7.0+ |
| **Authentication** | fastapi-users | 12.1.0+ |
| **JWT** | python-jose | 3.5.0+ |
| **Caching** | Redis (asyncio) | 5.0.0+ |
| **Password Hashing** | bcrypt (passlib) | 1.7.4+ |
| **Testing** | pytest + pytest-asyncio | 9.0.3+ |
| **Containerization** | Docker/Docker Compose | Latest |
| **Server** | Uvicorn | 0.29.0+ |

### Architecture Summary

LayerMap Back follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│                    (Web Frontend, External Apps)                │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application (app/main.py)            │  │
│  │  - CORS Middleware                                        │  │
│  │  - Exception Handlers                                     │  │
│  │  - Dependency Injection                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │  Auth Router│ │Projects Router│ │Sources Router│ │RPI Router│  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ Dependency Injection
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │  Projects   │ │  Sources    │ │ SourceTables  │ │ RPI      │  │
│  │  Service    │ │  Service    │ │  Service      │ │ Mapping  │  │
│  │             │ │             │ │               │ │ Service  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Users Service (fastapi-users)                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ Async Session
┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Layer                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM Models                        │  │
│  │  - User, Project, ProjectMember                           │  │
│  │  - Source, SourceTable, SourceColumn                      │  │
│  │  - RPIMapping                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ asyncpg
┌─────────────────────────────────────────────────────────────────┐
│                         Database                                │
│                    PostgreSQL 16+                               │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         Cache                                   │
│                    Redis 7+                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

- **Dependency Injection**: FastAPI's `Depends()` for DB sessions, authentication, and authorization
- **Repository Pattern**: Service layer abstracts database operations
- **CQRS-like**: Separate Pydantic schemas for Create, Update, and Read operations
- **Async/Await**: All database and Redis operations are asynchronous
- **Singleton Pattern**: Redis connection pool and client instances
- **Factory Pattern**: Test factories in `tests/factories.py` for test data generation

---

## 2. Getting Started

### Prerequisites

- **Python**: 3.13 or higher
- **PostgreSQL**: 16 or higher (or Docker)
- **Redis**: 7 or higher (or Docker)
- **Git**: For cloning the repository
- **Docker & Docker Compose**: For local development (recommended)

### Step-by-Step Local Setup

#### Option 1: Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/org/layermap-back.git
   cd layermap-back
   ```

2. **Start database and cache services**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Install Python dependencies**
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API documentation**
   - OpenAPI Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

#### Option 2: Manual Setup

1. **Clone and install dependencies** (same as above)

2. **Create PostgreSQL database**
   ```bash
   createdb -U postgres rpi_db
   ```

3. **Configure environment variables** (see table below)

4. **Run migrations** (same as above)

5. **Start the server** (same as above)

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:password@localhost/rpi_db` | PostgreSQL connection string with asyncpg driver |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL for caching |
| `CACHE_TTL` | No | `300` | Default cache time-to-live in seconds |
| `JWT_SECRET_KEY` | Yes | `your-super-secret-key-change-in-production` | Secret key for JWT token signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm (HS256, HS384, HS512) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token expiration time |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | JWT refresh token expiration time |
| `DEBUG` | No | `False` | Enable debug mode (more verbose logging) |
| `APP_TITLE` | No | `LayerMap Back` | API title shown in documentation |
| `APP_VERSION` | No | `0.1.0` | API version |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Comma-separated list of allowed CORS origins |
| `REDIS_MAX_CONNECTIONS` | No | `10` | Maximum Redis connection pool size |

### Creating a `.env` File

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rpi_db
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=True
APP_TITLE=LayerMap Back
APP_VERSION=0.1.0
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
REDIS_MAX_CONNECTIONS=10
```

---

## 3. Project Structure

```
layermap-back/
├── alembic/                          # Database migrations
│   ├── env.py                        # Alembic configuration
│   ├── script.py.mako                # Migration template
│   └── versions/                     # Migration files
│       ├── 94aca1390145_init.py      # Initial schema
│       ├── 35bc1c36160b_unique_proj_name.py
│       ├── 001_fix_measurement_type_enum.py
│       ├── 5c43b21311b9_add_users_table.py
│       ├── ba526ac7dd21_fastapi_users.py
│       └── ... (12+ migration files)
├── app/                              # Application code
│   ├── core/                         # Core modules
│   │   ├── auth.py                   # Authentication setup (fastapi-users)
│   │   ├── cache.py                  # Redis caching layer
│   │   ├── config.py                 # Pydantic settings
│   │   ├── dependencies.py           # Common dependencies
│   │   ├── middleware.py             # Custom CORS middleware
│   │   ├── security.py               # Password hashing utilities
│   │   ├── user_manager.py           # User manager for fastapi-users
│   │   └── utils.py                  # Utility functions
│   ├── database.py                   # SQLAlchemy engine & session
│   ├── main.py                       # FastAPI application entry point
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                   # User model (fastapi-users)
│   │   ├── project.py                # Project model
│   │   ├── project_member.py         # Project membership model
│   │   ├── source.py                 # Data source model
│   │   ├── source_table.py           # Source table & column models
│   │   └── rpi_mapping.py            # RPI mapping model
│   ├── routers/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                   # Authentication endpoints
│   │   ├── projects.py               # Project CRUD endpoints
│   │   ├── sources.py                # Source CRUD endpoints
│   │   ├── source_tables.py          # Source table CRUD endpoints
│   │   └── rpi_mappings.py           # RPI mapping endpoints
│   ├── schemas/                      # Pydantic DTOs
│   │   ├── __init__.py
│   │   ├── user.py                   # User schemas
│   │   ├── project.py                # Project schemas
│   │   ├── source.py                 # Source schemas
│   │   ├── source_table.py           # Source table schemas
│   │   └── rpi_mapping.py            # RPI mapping schemas
│   └── services/                     # Business logic
│       ├── __init__.py
│       ├── users.py                  # User service
│       ├── projects.py               # Project service
│       ├── sources.py                # Source service
│       ├── source_tables.py          # Source table service
│       └── rpi_mappings.py           # RPI mapping service
├── tests/                            # Test suite
│   ├── conftest.py                   # Pytest fixtures & configuration
│   ├── factories.py                  # Test data factories
│   ├── utils.py                      # Test utilities
│   ├── test_health.py                # Health check tests
│   ├── test_cache.py                 # Cache layer tests
│   ├── test_errors.py                # Error handling tests
│   ├── test_projects_api.py          # Projects API tests
│   ├── test_sources_api.py           # Sources API tests
│   ├── test_source_tables_api.py     # Source tables API tests
│   ├── test_rpi_mappings_api.py      # RPI mappings API tests
│   ├── test_contract.py              # Contract validation tests
│   ├── test_functional_enhanced.py   # Enhanced functional tests
│   ├── test_security_api.py          # Security tests
│   └── test_performance_api.py       # Performance tests
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
├── docker-compose.yaml               # Docker services definition
├── pyproject.toml                    # Project metadata & tool config
├── requirements.txt                  # Python dependencies
├── DOCUMENTATION.md                  # This documentation file
└── README.md                         # Project README
```

### Key Files and Responsibilities

| File | Responsibility |
|------|----------------|
| [`app/main.py`](app/main.py) | FastAPI app factory, middleware setup, router registration, lifespan management |
| [`app/core/config.py`](app/core/config.py) | Pydantic-based settings with environment variable loading |
| [`app/core/auth.py`](app/core/auth.py) | JWT authentication setup, user strategy, ACL dependencies |
| [`app/core/cache.py`](app/core/cache.py) | Redis caching with pattern-based invalidation |
| [`app/database.py`](app/database.py) | Async SQLAlchemy engine, session factory, dependency |
| [`app/models/*.py`](app/models/) | SQLAlchemy ORM models with relationships and constraints |
| [`app/schemas/*.py`](app/schemas/) | Pydantic v2 DTOs for request validation and response serialization |
| [`app/routers/*.py`](app/routers/) | HTTP route handlers with dependency injection |
| [`app/services/*.py`](app/services/) | Business logic, database operations, cache invalidation |
| [`alembic/env.py`](alembic/env.py) | Alembic configuration for migrations |
| [`tests/conftest.py`](tests/conftest.py) | Pytest fixtures for DB, auth, Redis mocking |
| [`tests/factories.py`](tests/factories.py) | Test data factories for creating test entities |

---

## 4. API / Routes Reference

### Base URL

All endpoints are relative to the server root. Example: `http://localhost:8000`

### Authentication Endpoints

#### `POST /auth/register`

**Description:** Register a new user account

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| email | body | string | Yes | User email (must be unique) |
| password | body | string | Yes | User password (min 8 characters) |
| full_name | body | string | No | User's full name |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | User ID |
| email | string | User email |
| full_name | string | User's full name |
| is_active | bool | Whether user is active |
| is_superuser | bool | Whether user is superuser |
| is_verified | bool | Whether user is verified |

**Example request:**
```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Example response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

**Error codes:** 400 — invalid input, 409 — email already exists

---

#### `POST /auth/jwt/login`

**Description:** Authenticate and receive JWT tokens

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| username | body | string | Yes | User email |
| password | body | string | Yes | User password |
| grant_type | body | string | Yes | Must be `password` |
| scope | body | string | No | OAuth scopes (optional) |
| client_id | body | string | No | Client ID (optional) |
| client_secret | body | string | No | Client secret (optional) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT access token |
| refresh_token | string | JWT refresh token |
| token_type | string | Always `bearer` |

**Example request:**
```http
POST /auth/jwt/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123&grant_type=password
```

**Example response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error codes:** 400 — invalid credentials, 401 — authentication failed

---

#### `POST /auth/refresh`

**Description:** Refresh access token using refresh token

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| refresh_token | body | string | Yes | Valid refresh token |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | New JWT access token |
| refresh_token | string | New refresh token |
| token_type | string | Always `bearer` |

**Example request:**
```http
POST /auth/refresh HTTP/1.1
Content-Type: application/x-www-form-urlencoded

refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 400 — invalid refresh token, 401 — token expired

---

#### `GET /auth/me`

**Description:** Get current authenticated user information

**Auth required:** Yes (Bearer token)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | header | string | Yes | Bearer token |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | User ID |
| email | string | User email |
| full_name | string | User's full name |
| is_active | bool | Whether user is active |
| is_superuser | bool | Whether user is superuser |
| is_verified | bool | Whether user is verified |

**Example request:**
```http
GET /auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 404 — user not found

---

### Projects Endpoints

#### `GET /projects`

**Description:** Get list of all projects with optional pagination

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| skip | query | int | No | Number of projects to skip (default: 0) |
| limit | query | int | No | Max projects to return (default: 20, max: 100) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status (active, draft, archived) |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects?skip=0&limit=10 HTTP/1.1
```

**Example response:**
```json
[
  {
    "id": 1,
    "name": "Project A",
    "description": "Test project",
    "status": "active",
    "created_at": "2026-04-17T13:25:03.970536",
    "updated_at": "2026-04-17T13:25:03.970536"
  }
]
```

**Error codes:** 400 — invalid pagination params

---

#### `POST /projects`

**Description:** Create a new project

**Auth required:** Yes (Bearer token)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| name | body | string | Yes | Project name (must be unique) |
| description | body | string | No | Project description |
| status | body | string | No | Project status (default: draft) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /projects HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "status": "active"
}
```

**Example response:**
```json
{
  "id": 2,
  "name": "New Project",
  "description": "Project description",
  "status": "active",
  "created_at": "2026-04-20T10:00:00.000000",
  "updated_at": "2026-04-20T10:00:00.000000"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 409 — project name already exists

---

#### `GET /projects/{project_id}`

**Description:** Get a specific project by ID

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — project not found

---

#### `PUT /projects/{project_id}`

**Description:** Update a project (owner or editor only)

**Auth required:** Yes (owner or editor)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |
| name | body | string | No | New project name |
| description | body | string | No | New description |
| status | body | string | No | New status |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Project ID |
| name | string | Project name |
| description | string | Project description |
| status | string | Project status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PUT /projects/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Updated Project",
  "status": "archived"
}
```

**Error codes:** 401 — unauthorized, 403 — insufficient permissions, 404 — project not found, 409 — project name already exists

---

#### `DELETE /projects/{project_id}`

**Description:** Delete a project (owner only)

**Auth required:** Yes (owner only)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted project ID |
| name | string | Deleted project name |

**Example request:**
```http
DELETE /projects/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example response:**
```json
{
  "id": 1,
  "name": "Deleted Project"
}
```

**Error codes:** 401 — unauthorized, 403 — not the owner, 404 — project not found

---

#### `GET /projects/{project_id}/members`

**Description:** Get project members list

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Membership ID |
| user_id | int | User ID |
| project_id | int | Project ID |
| role | string | User role (owner, editor, viewer) |
| created_at | datetime | Membership creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /projects/1/members HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — project not found

---

#### `POST /projects/{project_id}/members`

**Description:** Add a member to a project (owner only)

**Auth required:** Yes (owner only)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |
| user_id | body | int | Yes | User ID to add |
| role | body | string | Yes | Role (owner, editor, viewer) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Membership ID |
| user_id | int | User ID |
| project_id | int | Project ID |
| role | string | User role |
| created_at | datetime | Membership creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /projects/1/members HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_id": 2,
  "role": "editor"
}
```

**Error codes:** 400 — invalid role, 401 — unauthorized, 403 — not the owner, 404 — project or user not found, 409 — user already a member

---

#### `PUT /projects/{project_id}/members/{membership_id}`

**Description:** Update a member's role (owner only)

**Auth required:** Yes (owner only)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |
| membership_id | path | int | Yes | Membership ID |
| role | body | string | Yes | New role (owner, editor, viewer) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Membership ID |
| user_id | int | User ID |
| project_id | int | Project ID |
| role | string | Updated role |
| created_at | datetime | Membership creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PUT /projects/1/members/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "role": "editor"
}
```

**Error codes:** 400 — invalid role, 401 — unauthorized, 403 — not the owner, 404 — membership not found

---

#### `DELETE /projects/{project_id}/members/{membership_id}`

**Description:** Remove a member from a project (owner only)

**Auth required:** Yes (owner only)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |
| membership_id | path | int | Yes | Membership ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted membership ID |
| user_id | int | Deleted user ID |
| project_id | int | Deleted project ID |

**Example request:**
```http
DELETE /projects/1/members/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not the owner, 404 — membership not found

---

#### `GET /projects/{project_id}/kpi`

**Description:** Get project KPI statistics

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | path | int | Yes | Project ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| total_mappings | int | Total RPI mappings count |
| approved_mappings | int | Approved mappings count |
| in_review_mappings | int | In review mappings count |
| draft_mappings | int | Draft mappings count |
| calculated_mappings | int | Calculated mappings count |
| total_ownership | int | Total ownership count |
| total_sources | int | Total sources count |
| total_tables | int | Total source tables count |

**Example request:**
```http
GET /projects/1/kpi HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example response:**
```json
{
  "total_mappings": 150,
  "approved_mappings": 80,
  "in_review_mappings": 40,
  "draft_mappings": 30,
  "calculated_mappings": 25,
  "total_ownership": 45,
  "total_sources": 10,
  "total_tables": 25
}
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — project not found

---

### Sources Endpoints

#### `GET /sources`

**Description:** Get list of all sources with optional pagination

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| skip | query | int | No | Number of sources to skip (default: 0) |
| limit | query | int | No | Max sources to return (default: 20, max: 100) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source ID |
| project_id | int | Project ID |
| mapping_table_id | int | Mapping table ID (nullable) |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type (API, DB, FILE, STREAM) |
| row_count | int | Number of rows |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /sources?skip=0&limit=10 HTTP/1.1
```

**Error codes:** 400 — invalid pagination params

---

#### `POST /sources`

**Description:** Create a new source

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | body | int | Yes | Project ID |
| mapping_table_id | body | int | No | Mapping table ID |
| name | body | string | Yes | Source name |
| description | body | string | No | Source description |
| type | body | string | Yes | Source type (API, DB, FILE, STREAM) |
| row_count | body | int | No | Row count (default: 0) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source ID |
| project_id | int | Project ID |
| mapping_table_id | int | Mapping table ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | int | Row count |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
POST /sources HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "project_id": 1,
  "name": "Production DB",
  "type": "DB",
  "description": "Main production database"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 404 — project not found

---

#### `GET /sources/{source_id}`

**Description:** Get a specific source by ID

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| source_id | path | int | Yes | Source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source ID |
| project_id | int | Project ID |
| mapping_table_id | int | Mapping table ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | int | Row count |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /sources/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — source not found

---

#### `PUT /sources/{source_id}`

**Description:** Update a source (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| source_id | path | int | Yes | Source ID |
| name | body | string | No | New name |
| description | body | string | No | New description |
| type | body | string | No | New type |
| row_count | body | int | No | New row count |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source ID |
| project_id | int | Project ID |
| mapping_table_id | int | Mapping table ID |
| name | string | Source name |
| description | string | Source description |
| type | string | Source type |
| row_count | int | Row count |
| last_updated | datetime | Last update timestamp |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
PUT /sources/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Updated Source",
  "row_count": 1000000
}
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — source not found

---

#### `DELETE /sources/{source_id}`

**Description:** Delete a source (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| source_id | path | int | Yes | Source ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted source ID |
| name | string | Deleted source name |

**Example request:**
```http
DELETE /sources/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — source not found

---

### Source Tables Endpoints

#### `GET /source-tables`

**Description:** Get list of all source tables with optional pagination

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| skip | query | int | No | Number of tables to skip (default: 0) |
| limit | query | int | No | Max tables to return (default: 20, max: 100) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source table ID |
| source_id | int | Source ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /source-tables?skip=0&limit=10 HTTP/1.1
```

**Error codes:** 400 — invalid pagination params

---

#### `POST /source-tables`

**Description:** Create a new source table

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| source_id | body | int | Yes | Source ID |
| name | body | string | Yes | Table name |
| description | body | string | No | Table description |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source table ID |
| source_id | int | Source ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /source-tables HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "source_id": 1,
  "name": "customers",
  "description": "Customer data table"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 404 — source not found

---

#### `GET /source-tables/{table_id}`

**Description:** Get a specific source table by ID

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source table ID |
| source_id | int | Source ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /source-tables/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — table not found

---

#### `PUT /source-tables/{table_id}`

**Description:** Update a source table (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |
| name | body | string | No | New name |
| description | body | string | No | New description |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Source table ID |
| source_id | int | Source ID |
| name | string | Table name |
| description | string | Table description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PUT /source-tables/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "updated_customers",
  "description": "Updated customer data"
}
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — table not found

---

#### `DELETE /source-tables/{table_id}`

**Description:** Delete a source table (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted table ID |
| name | string | Deleted table name |

**Example request:**
```http
DELETE /source-tables/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — table not found

---

#### `GET /source-tables/{table_id}/columns`

**Description:** Get all columns for a source table

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Column ID |
| source_table_id | int | Source table ID |
| name | string | Column name |
| type | string | Column type (dimension, metric) |
| data_type | string | SQL data type |
| description | string | Column description |
| is_calculated | bool | Whether column is calculated |
| formula | string | Calculation formula (nullable) |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
GET /source-tables/1/columns HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — table not found

---

#### `POST /source-tables/{table_id}/columns`

**Description:** Create a new column for a source table

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |
| name | body | string | Yes | Column name |
| type | body | string | Yes | Column type (dimension, metric) |
| data_type | body | string | Yes | SQL data type |
| description | body | string | No | Column description |
| is_calculated | body | bool | No | Whether column is calculated (default: false) |
| formula | body | string | No | Calculation formula (required if is_calculated=true) |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Column ID |
| source_table_id | int | Source table ID |
| name | string | Column name |
| type | string | Column type |
| data_type | string | SQL data type |
| description | string | Column description |
| is_calculated | bool | Whether column is calculated |
| formula | string | Calculation formula |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
POST /source-tables/1/columns HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "customer_id",
  "type": "dimension",
  "data_type": "integer",
  "description": "Customer unique identifier"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 403 — not a project member, 404 — table not found

---

#### `PUT /source-tables/{table_id}/columns/{column_id}`

**Description:** Update a source table column

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |
| column_id | path | int | Yes | Column ID |
| name | body | string | No | New name |
| type | body | string | No | New type |
| data_type | body | string | No | New data type |
| description | body | string | No | New description |
| is_calculated | body | bool | No | New calculated status |
| formula | body | string | No | New formula |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Column ID |
| source_table_id | int | Source table ID |
| name | string | Column name |
| type | string | Column type |
| data_type | string | SQL data type |
| description | string | Column description |
| is_calculated | bool | Whether column is calculated |
| formula | string | Calculation formula |
| created_at | datetime | Creation timestamp |

**Example request:**
```http
PUT /source-tables/1/columns/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "updated_customer_id",
  "description": "Updated description"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 403 — not a project member, 404 — column not found

---

#### `DELETE /source-tables/{table_id}/columns/{column_id}`

**Description:** Delete a source table column

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| table_id | path | int | Yes | Source table ID |
| column_id | path | int | Yes | Column ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted column ID |
| name | string | Deleted column name |

**Example request:**
```http
DELETE /source-tables/1/columns/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — column not found

---

### RPI Mappings Endpoints

#### `GET /rpi-mappings`

**Description:** Get list of all RPI mappings with optional filters and pagination

**Auth required:** No

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| skip | query | int | No | Number of mappings to skip (default: 0) |
| limit | query | int | No | Max mappings to return (default: 20, max: 100) |
| status | query | string | No | Filter by status (approved, in_review, draft) |
| ownership | query | string | No | Filter by ownership |
| measurement_type | query | string | No | Filter by type (dimension, metric) |
| dimension | query | string | No | Filter by dimension name (partial match) |
| is_calculated | query | bool | No | Filter by calculated status |
| search | query | string | No | Search in measurement, dimension, object_field, ownership |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Mapping ID |
| number | int | RPI number (nullable) |
| project_id | int | Project ID |
| source_column_id | int | Source column ID (nullable) |
| ownership | string | Ownership attribution |
| status | string | Status (approved, in_review, draft) |
| block | string | Block name (nullable) |
| measurement_type | string | Type (dimension, metric, nullable) |
| dimension | string | Dimension name (nullable) |
| is_calculated | bool | Whether calculated |
| formula | string | Calculation formula (nullable) |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report name |
| object_field | string | Object field name |
| date_added | date | Date added (nullable) |
| date_removed | date | Date removed (nullable) |
| comment | string | Comment (nullable) |
| verification_file | string | Verification file path |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /rpi-mappings?skip=0&limit=10&status=approved&measurement_type=metric HTTP/1.1
```

**Error codes:** 400 — invalid filter params

---

#### `POST /rpi-mappings`

**Description:** Create a new RPI mapping

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| project_id | body | int | Yes | Project ID |
| number | body | int | No | RPI number |
| source_column_id | body | int | No | Source column ID |
| ownership | body | string | No | Ownership attribution |
| status | body | string | No | Status (default: draft) |
| block | body | string | No | Block name |
| measurement_type | body | string | No | Type (dimension, metric) — опционально |
| dimension | body | string | No | Dimension name (измерение) |
| is_calculated | body | bool | No | Whether calculated (default: false) |
| formula | body | string | No | Calculation formula (required if is_calculated=true) |
| measurement | body | string | Yes | Measurement name |
| measurement_description | body | string | No | Measurement description |
| source_report | body | string | No | Source report name |
| object_field | body | string | Yes | Object field name |
| date_added | body | string | No | Date added (YYYY-MM-DD) |
| date_removed | body | string | No | Date removed (YYYY-MM-DD) |
| comment | body | string | No | Comment |
| verification_file | body | string | No | Verification file path |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Mapping ID |
| number | int | RPI number |
| project_id | int | Project ID |
| source_column_id | int | Source column ID |
| ownership | string | Ownership attribution |
| status | string | Status |
| block | string | Block name |
| measurement_type | string | Type |
| is_calculated | bool | Whether calculated |
| formula | string | Calculation formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report name |
| object_field | string | Object field name |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file path |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
POST /rpi-mappings HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "project_id": 1,
  "measurement_type": "metric",
  "measurement": "Выручка",
  "object_field": "revenue",
  "ownership": "Финансовый департамент",
  "status": "draft",
  "is_calculated": false
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 404 — project not found

---

#### `GET /rpi-mappings/{mapping_id}`

**Description:** Get a specific RPI mapping by ID

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| mapping_id | path | int | Yes | Mapping ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Mapping ID |
| number | int | RPI number |
| project_id | int | Project ID |
| source_column_id | int | Source column ID |
| ownership | string | Ownership attribution |
| status | string | Status |
| block | string | Block name |
| measurement_type | string | Type (nullable) |
| dimension | string | Dimension name (nullable) |
| is_calculated | bool | Whether calculated |
| formula | string | Calculation formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report name |
| object_field | string | Object field name |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file path |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
GET /rpi-mappings/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — mapping not found

---

#### `PUT /rpi-mappings/{mapping_id}`

**Description:** Update an RPI mapping (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| mapping_id | path | int | Yes | Mapping ID |
| number | body | int | No | New RPI number |
| source_column_id | body | int | No | New source column ID |
| ownership | body | string | No | New ownership |
| status | body | string | No | New status |
| block | body | string | No | New block name |
| measurement_type | body | string | No | New type (nullable) |
| dimension | body | string | No | New dimension name |
| is_calculated | body | bool | No | New calculated status |
| formula | body | string | No | New formula |
| measurement | body | string | No | New measurement name |
| measurement_description | body | string | No | New description |
| source_report | body | string | No | New source report |
| object_field | body | string | No | New object field |
| date_added | body | string | No | New date added |
| date_removed | body | string | No | New date removed |
| comment | body | string | No | New comment |
| verification_file | body | string | No | New verification file |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Mapping ID |
| number | int | RPI number |
| project_id | int | Project ID |
| source_column_id | int | Source column ID |
| ownership | string | Ownership attribution |
| status | string | Status |
| block | string | Block name |
| measurement_type | string | Type (nullable) |
| dimension | string | Dimension name (nullable) |
| is_calculated | bool | Whether calculated |
| formula | string | Calculation formula |
| measurement | string | Measurement name |
| measurement_description | string | Measurement description |
| source_report | string | Source report name |
| object_field | string | Object field name |
| date_added | date | Date added |
| date_removed | date | Date removed |
| comment | string | Comment |
| verification_file | string | Verification file path |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Example request:**
```http
PUT /rpi-mappings/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "in_review",
  "comment": "Updated for review"
}
```

**Error codes:** 400 — invalid input, 401 — unauthorized, 403 — not a project member, 404 — mapping not found

---

#### `DELETE /rpi-mappings/{mapping_id}`

**Description:** Delete an RPI mapping (any project member)

**Auth required:** Yes (any authenticated member)

**Request**
| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| mapping_id | path | int | Yes | Mapping ID |

**Response**
| Field | Type | Description |
|-------|------|-------------|
| id | int | Deleted mapping ID |
| measurement | string | Deleted measurement name |

**Example request:**
```http
DELETE /rpi-mappings/1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Error codes:** 401 — unauthorized, 403 — not a project member, 404 — mapping not found

---

## 5. Data Models & Schemas

### Database Schema

#### ER Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string full_name
        string hashed_password
        bool is_active
        bool is_superuser
        bool is_verified
        datetime created_at
        datetime updated_at
    }

    PROJECTS {
        int id PK
        string name UK
        text description
        string status
        datetime created_at
        datetime updated_at
    }

    PROJECT_MEMBERS {
        int id PK
        int user_id FK
        int project_id FK
        string role
        datetime created_at
        datetime updated_at
    }

    SOURCES {
        int id PK
        int project_id FK
        int mapping_table_id FK
        string name
        text description
        string type
        bigint row_count
        datetime last_updated
        datetime created_at
    }

    MAPPING_TABLES {
        int id PK
        int project_id FK
        int source_id FK
        string name
        text description
        datetime created_at
        datetime updated_at
    }

    MAPPING_COLUMNS {
        int id PK
        int mapping_table_id FK
        string name
        string type
        string data_type
        text description
        bool is_calculated
        text formula
        datetime created_at
    }

    SOURCE_TABLES {
        int id PK
        int source_id FK
        string name
        text description
        datetime created_at
        datetime updated_at
    }

    SOURCE_COLUMNS {
        int id PK
        int source_table_id FK
        string name
        string type
        string data_type
        text description
        bool is_calculated
        text formula
        datetime created_at
    }

    RPI_MAPPINGS {
        int id PK
        int number
        int project_id FK
        int source_column_id FK
        string ownership
        string status
        string block
        string measurement_type
        bool is_calculated
        text formula
        string measurement
        text measurement_description
        string source_report
        string object_field
        date date_added
        date date_removed
        text comment
        string verification_file
        datetime created_at
        datetime updated_at
    }

    USERS ||--o{ PROJECT_MEMBERS : "belongs to"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has members"
    PROJECTS ||--o{ SOURCES : "owns"
    PROJECTS ||--o{ MAPPING_TABLES : "owns"
    PROJECTS ||--o{ RPI_MAPPINGS : "contains"
    SOURCES ||--o{ MAPPING_TABLES : "contains"
    SOURCES ||--o{ SOURCE_TABLES : "contains"
    MAPPING_TABLES ||--o{ MAPPING_COLUMNS : "contains"
    SOURCE_TABLES ||--o{ SOURCE_COLUMNS : "contains"
    SOURCE_COLUMNS ||--o| RPI_MAPPINGS : "maps to"
```

### Model: User

**File:** [`app/models/user.py`](app/models/user.py:1)

**Table:** `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | User ID |
| `email` | `str` | Unique, Not Null | User email address |
| `full_name` | `str` | Nullable | User's full name |
| `hashed_password` | `str` | Not Null | Bcrypt-hashed password |
| `is_active` | `bool` | Default: True | Whether user account is active |
| `is_superuser` | `bool` | Default: False | Whether user has admin privileges |
| `is_verified` | `bool` | Default: False | Whether user email is verified |
| `created_at` | `datetime` | Server default: now() | Account creation timestamp |
| `updated_at` | `datetime` | Server default: now() | Last update timestamp |

**Pydantic Schemas:** [`app/schemas/user.py`](app/schemas/user.py)

- `UserCreate` — Registration request
- `UserUpdate` — Profile update request
- `UserUpdatePassword` — Password change request
- `UserRegister` — Full registration with email/password
- `User` — Read model (all fields)
- `UserOut` — Public read model (excludes hashed_password)

---

### Model: Project

**File:** [`app/models/project.py`](app/models/project.py:1)

**Table:** `projects`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Project ID |
| `name` | `str` | Unique, Not Null | Project name |
| `description` | `str` | Nullable (Text) | Project description |
| `status` | `ProjectStatus` | Not Null, Default: draft | Project status |
| `created_at` | `datetime` | Server default: now() | Creation timestamp |
| `updated_at` | `datetime` | Server default: now() | Last update timestamp |

**Enum: `ProjectStatus`**
- `active` — Project is active
- `draft` — Project is in draft
- `archived` — Project is archived

**Pydantic Schemas:** [`app/schemas/project.py`](app/schemas/project.py)

- `ProjectCreate` — Create request
- `ProjectUpdate` — Update request
- `ProjectOut` — Read model
- `ProjectKPI` — KPI statistics response

---

### Model: ProjectMember

**File:** [`app/models/project_member.py`](app/models/project_member.py:1)

**Table:** `project_members`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Membership ID |
| `user_id` | `int` | FK → users.id, Not Null | User ID |
| `project_id` | `int` | FK → projects.id, Not Null | Project ID |
| `role` | `str` | Not Null | User role |
| `created_at` | `datetime` | Server default: now() | Membership creation timestamp |
| `updated_at` | `datetime` | Server default: now() | Last update timestamp |

**Unique Constraint:** `(user_id, project_id)` — One membership per user per project

**Enum: `ProjectRole`**
- `owner` — Project owner (full permissions)
- `editor` — Project editor (can update)
- `viewer` — Project viewer (read-only)

**Pydantic Schemas:** [`app/schemas/project.py`](app/schemas/project.py:100)

- `ProjectMemberCreate` — Create membership request
- `ProjectMemberUpdate` — Update membership request
- `ProjectMemberOut` — Read model

---

### Model: Source

**File:** [`app/models/source.py`](app/models/source.py:1)

**Table:** `sources`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Source ID |
| `project_id` | `int` | FK → projects.id, Not Null, Cascade delete | Project ID |
| `mapping_table_id` | `int` | FK → mapping_tables.id, Nullable, Set null | Mapping table reference |
| `name` | `str` | Not Null | Source name |
| `description` | `str` | Nullable (Text) | Source description |
| `type` | `SourceType` | Not Null | Source type |
| `row_count` | `int` | Not Null, Default: 0 | Number of rows |
| `last_updated` | `datetime` | Nullable | Last data update timestamp |
| `created_at` | `datetime` | Server default: now() | Creation timestamp |

**Enum: `SourceType`**
- `API` — REST/GraphQL API
- `DB` — Database connection
- `FILE` — File-based source (CSV, Excel, etc.)
- `STREAM` — Real-time data stream

**Pydantic Schemas:** [`app/schemas/source.py`](app/schemas/source.py)

- `SourceCreate` — Create request
- `SourceUpdate` — Update request
- `SourceOut` — Read model

---

### Model: SourceTable

**File:** [`app/models/source_table.py`](app/models/source_table.py:1)

**Table:** `source_tables`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Source table ID |
| `source_id` | `int` | FK → sources.id, Not Null, Cascade delete | Source ID |
| `name` | `str` | Not Null | Table name |
| `description` | `str` | Nullable (Text) | Table description |
| `created_at` | `datetime` | Server default: now() | Creation timestamp |
| `updated_at` | `datetime` | Server default: now() | Last update timestamp |

**Pydantic Schemas:** [`app/schemas/source_table.py`](app/schemas/source_table.py)

- `SourceTableCreate` — Create request
- `SourceTableUpdate` — Update request
- `SourceTableOut` — Read model

---

### Model: SourceColumn

**File:** [`app/models/source_table.py`](app/models/source_table.py:50)

**Table:** `source_columns`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Column ID |
| `source_table_id` | `int` | FK → source_tables.id, Not Null, Cascade delete | Source table ID |
| `name` | `str` | Not Null | Column name |
| `type` | `ColumnType` | Not Null | Column type |
| `data_type` | `str` | Not Null | SQL data type |
| `description` | `str` | Nullable (Text) | Column description |
| `is_calculated` | `bool` | Not Null, Default: false | Whether column is calculated |
| `formula` | `str` | Nullable (Text) | Calculation formula |
| `created_at` | `datetime` | Server default: now() | Creation timestamp |

**Enum: `ColumnType`**
- `dimension` — Dimension column
- `metric` — Metric column

**Pydantic Schemas:** [`app/schemas/source_table.py`](app/schemas/source_table.py:50)

- `SourceColumnCreate` — Create request
- `SourceColumnUpdate` — Update request
- `SourceColumnOut` — Read model

---

### Model: RPIMapping

**File:** [`app/models/rpi_mapping.py`](app/models/rpi_mapping.py:1)

**Table:** `rpi_mappings`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, Auto-increment | Mapping ID |
| `number` | `int` | Nullable | RPI number |
| `project_id` | `int` | FK → projects.id, Not Null, Cascade delete | Project ID |
| `source_column_id` | `int` | FK → source_columns.id, Nullable, Set null | Source column reference |
| `ownership` | `str` | Nullable (128 chars) | Ownership attribution |
| `status` | `RPIStatus` | Not Null, Default: draft | Status |
| `block` | `str` | Nullable (128 chars) | Block name |
| `measurement_type` | `MeasurementType` | Nullable | Type (dimension/metric, now optional) |
| `dimension` | `str` | Nullable (255 chars) | Dimension name (измерение) |
| `is_calculated` | `bool` | Not Null, Default: false | Whether calculated |
| `formula` | `str` | Nullable (Text) | Calculation formula |
| `measurement` | `str` | Not Null (255 chars) | Measurement name |
| `measurement_description` | `str` | Nullable (Text) | Measurement description |
| `source_report` | `str` | Nullable (255 chars) | Source report name |
| `object_field` | `str` | Not Null (255 chars) | Object field name |
| `date_added` | `date` | Nullable | Date added |
| `date_removed` | `date` | Nullable | Date removed |
| `comment` | `str` | Nullable (Text) | Comment |
| `verification_file` | `str` | Nullable (512 chars) | Verification file path |
| `created_at` | `datetime` | Server default: now() | Creation timestamp |
| `updated_at` | `datetime` | Server default: now() | Last update timestamp |

**Check Constraint:** `chk_formula` — `(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)`

**Enum: `RPIStatus`**
- `approved` — Approved for use
- `in_review` — Under review
- `draft` — Draft status

**Enum: `MeasurementType`** (опционально, для обратной совместимости)
- `dimension` — Измерение
- `metric` — Метрика/показатель

**Новое поле:** `dimension` (VARCHAR(255), nullable) — название измерения, независимое от `measurement`. Каждая строка RPI может одновременно содержать и измерение (`dimension`), и показатель (`measurement`).

**Pydantic Schemas:** [`app/schemas/rpi_mapping.py`](app/schemas/rpi_mapping.py)

- `RPIMappingCreate` — Create request
- `RPIMappingUpdate` — Update request
- `RPIMappingOut` — Read model
- `RPIMappingListFilter` — List filter parameters
- `RPIMappingKPI` — KPI statistics

---

## 6. Business Logic & Core Functions

### Service: Projects

**File:** [`app/services/projects.py`](app/services/projects.py:1)

#### `get_list(db: AsyncSession) -> list[Project]`

**Purpose:** Returns all projects ordered by creation date (descending).

**Parameters:**
- `db` — Async database session

**Returns:** List of `Project` objects

**Side effects:** Reads from cache, caches result for 60 seconds

**Usage:**
```python
projects = await get_list(db_session)
```

---

#### `get(db: AsyncSession, project_id: int) -> Project | None`

**Purpose:** Get a project by ID.

**Parameters:**
- `db` — Async database session
- `project_id` — Project ID

**Returns:** `Project` object or `None`

**Side effects:** None

**Usage:**
```python
project = await get(db_session, project_id=1)
```

---

#### `get_by_name(db: AsyncSession, name: str) -> Project | None`

**Purpose:** Get a project by name.

**Parameters:**
- `db` — Async database session
- `name` — Project name

**Returns:** `Project` object or `None`

**Side effects:** None

**Usage:**
```python
project = await get_by_name(db_session, "Project A")
```

---

#### `create(db: AsyncSession, payload: ProjectCreate, user_id: int) -> Project`

**Purpose:** Creates a new project and adds the user as owner.

**Parameters:**
- `db` — Async database session
- `payload` — `ProjectCreate` schema
- `user_id` — ID of user creating the project

**Returns:** Created `Project` object

**Side effects:** 
- Creates project record
- Creates project member record with owner role
- Invalidates project list cache

**Usage:**
```python
project = await create(db_session, ProjectCreate(name="New Project"), user_id=1)
```

---

#### `update(db: AsyncSession, project: Project, payload: ProjectUpdate) -> Project`

**Purpose:** Updates a project's fields.

**Parameters:**
- `db` — Async database session
- `project` — Project object to update
- `payload` — `ProjectUpdate` schema

**Returns:** Updated `Project` object

**Side effects:** Updates project record, invalidates cache

**Usage:**
```python
project = await update(db_session, project, ProjectUpdate(name="Updated"))
```

---

#### `delete(db: AsyncSession, project: Project) -> Project`

**Purpose:** Deletes a project and all related data.

**Parameters:**
- `db` — Async database session
- `project` — Project object to delete

**Returns:** Deleted `Project` object

**Side effects:** 
- Deletes project (cascade deletes sources, mappings, etc.)
- Invalidates all project-related caches

**Usage:**
```python
deleted = await delete(db_session, project)
```

---

#### `get_kpi(db: AsyncSession, project_id: int) -> dict`

**Purpose:** Calculates and returns KPI statistics for a project.

**Parameters:**
- `db` — Async database session
- `project_id` — Project ID

**Returns:** Dictionary with KPI metrics

**Side effects:** 
- Queries RPI mappings, sources, tables
- Caches result for 120 seconds

**Usage:**
```python
kpi = await get_kpi(db_session, project_id=1)
# {
#   "total_mappings": 150,
#   "approved_mappings": 80,
#   ...
# }
```

---

#### `add_member(db: AsyncSession, project: Project, user_id: int, role: ProjectRole) -> ProjectMember`

**Purpose:** Adds a member to a project.

**Parameters:**
- `db` — Async database session
- `project` — Project object
- `user_id` — User ID to add
- `role` — ProjectRole (owner, editor, viewer)

**Returns:** Created `ProjectMember` object

**Side effects:** Creates membership record

**Usage:**
```python
member = await add_member(db_session, project, user_id=2, role=ProjectRole.editor)
```

---

#### `update_member_role(db: AsyncSession, member: ProjectMember, role: ProjectRole) -> ProjectMember`

**Purpose:** Updates a member's role.

**Parameters:**
- `db` — Async database session
- `member` — ProjectMember object
- `role` — New role

**Returns:** Updated `ProjectMember` object

**Side effects:** Updates membership record

**Usage:**
```python
member = await update_member_role(db_session, member, ProjectRole.owner)
```

---

#### `remove_member(db: AsyncSession, member: ProjectMember) -> ProjectMember`

**Purpose:** Removes a member from a project.

**Parameters:**
- `db` — Async database session
- `member` — ProjectMember object to remove

**Returns:** Deleted `ProjectMember` object

**Side effects:** Deletes membership record

**Usage:**
```python
removed = await remove_member(db_session, member)
```

---

### Service: RPI Mappings

**File:** [`app/services/rpi_mappings.py`](app/services/rpi_mappings.py:1)

#### `get_list(db: AsyncSession, project_id: int, *, status: str | None = None, ownership: str | None = None, measurement_type: str | None = None, is_calculated: bool | None = None, search: str | None = None, skip: int = 0, limit: int = 20) -> list[RPIMapping]`

**Purpose:** Returns RPI mappings with filters and pagination.

**Parameters:**
- `db` — Async database session
- `project_id` — Project ID to filter by
- `status` — Optional status filter
- `ownership` — Optional ownership filter
- `measurement_type` — Optional type filter
- `dimension` — Optional dimension name filter (partial match)
- `is_calculated` — Optional calculated filter
- `search` — Optional search in measurement, dimension, object_field, ownership
- `skip` — Pagination offset (default: 0)
- `limit` — Pagination limit (default: 20)

**Returns:** List of `RPIMapping` objects

**Side effects:** 
- Applies filters and pagination
- Caches result for 60 seconds (pattern-based key)

**Usage:**
```python
mappings = await get_list(
    db_session,
    project_id=1,
    status="approved",
    measurement_type="metric",
    skip=0,
    limit=10
)
```

---

#### `get(db: AsyncSession, mapping_id: int) -> RPIMapping | None`

**Purpose:** Get a mapping by ID.

**Parameters:**
- `db` — Async database session
- `mapping_id` — Mapping ID

**Returns:** `RPIMapping` object or `None`

**Side effects:** None

**Usage:**
```python
mapping = await get(db_session, mapping_id=1)
```

---

#### `create(db: AsyncSession, project: Project, payload: RPIMappingCreate) -> RPIMapping`

**Purpose:** Creates a new RPI mapping.

**Parameters:**
- `db` — Async database session
- `project` — Project object
- `payload` — `RPIMappingCreate` schema

**Returns:** Created `RPIMapping` object

**Side effects:** 
- Creates mapping record
- Invalidates project RPI list cache

**Usage:**
```python
mapping = await create(db_session, project, RPIMappingCreate(
    measurement_type="metric",
    measurement="Выручка",
    object_field="revenue"
))
```

---

#### `update(db: AsyncSession, mapping: RPIMapping, payload: RPIMappingUpdate) -> RPIMapping`

**Purpose:** Updates an RPI mapping.

**Parameters:**
- `db` — Async database session
- `mapping` — Mapping object to update
- `payload` — `RPIMappingUpdate` schema

**Returns:** Updated `RPIMapping` object

**Side effects:** 
- Updates mapping record
- Invalidates cache

**Usage:**
```python
mapping = await update(db_session, mapping, RPIMappingUpdate(status="approved"))
```

---

#### `delete(db: AsyncSession, mapping: RPIMapping) -> RPIMapping`

**Purpose:** Deletes an RPI mapping.

**Parameters:**
- `db` — Async database session
- `mapping` — Mapping object to delete

**Returns:** Deleted `RPIMapping` object

**Side effects:** 
- Deletes mapping record
- Invalidates cache

**Usage:**
```python
deleted = await delete(db_session, mapping)
```

---

### Service: Sources

**File:** [`app/services/sources.py`](app/services/sources.py:1)

#### `get_list(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Source]`

**Purpose:** Returns all sources with pagination.

**Parameters:**
- `db` — Async database session
- `skip` — Pagination offset
- `limit` — Pagination limit

**Returns:** List of `Source` objects

**Side effects:** Caches result for 60 seconds

**Usage:**
```python
sources = await get_list(db_session, skip=0, limit=10)
```

---

#### `create(db: AsyncSession, project: Project, payload: SourceCreate) -> Source`

**Purpose:** Creates a new source.

**Parameters:**
- `db` — Async database session
- `project` — Project object
- `payload` — `SourceCreate` schema

**Returns:** Created `Source` object

**Side effects:** 
- Creates source record
- Invalidates project sources cache

**Usage:**
```python
source = await create(db_session, project, SourceCreate(
    name="Production DB",
    type=SourceType.DB
))
```

---

#### `update(db: AsyncSession, source: Source, payload: SourceUpdate) -> Source`

**Purpose:** Updates a source.

**Parameters:**
- `db` — Async database session
- `source` — Source object
- `payload` — `SourceUpdate` schema

**Returns:** Updated `Source` object

**Side effects:** Updates source record, invalidates cache

**Usage:**
```python
source = await update(db_session, source, SourceUpdate(row_count=1000000))
```

---

#### `delete(db: AsyncSession, source: Source) -> Source`

**Purpose:** Deletes a source.

**Parameters:**
- `db` — Async database session
- `source` — Source object

**Returns:** Deleted `Source` object

**Side effects:** 
- Deletes source (cascade deletes tables, columns)
- Invalidates cache

**Usage:**
```python
deleted = await delete(db_session, source)
```

---

### Service: Source Tables

**File:** [`app/services/source_tables.py`](app/services/source_tables.py:1)

#### `get_list(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[SourceTable]`

**Purpose:** Returns all source tables with pagination.

**Parameters:**
- `db` — Async database session
- `skip` — Pagination offset
- `limit` — Pagination limit

**Returns:** List of `SourceTable` objects

**Side effects:** Caches result for 60 seconds

**Usage:**
```python
tables = await get_list(db_session, skip=0, limit=10)
```

---

#### `get_by_source(db: AsyncSession, source_id: int) -> list[SourceTable]`

**Purpose:** Returns all tables for a source.

**Parameters:**
- `db` — Async database session
- `source_id` — Source ID

**Returns:** List of `SourceTable` objects

**Side effects:** None

**Usage:**
```python
tables = await get_by_source(db_session, source_id=1)
```

---

#### `create(db: AsyncSession, source: Source, payload: SourceTableCreate) -> SourceTable`

**Purpose:** Creates a new source table.

**Parameters:**
- `db` — Async database session
- `source` — Source object
- `payload` — `SourceTableCreate` schema

**Returns:** Created `SourceTable` object

**Side effects:** 
- Creates table record
- Invalidates source tables cache

**Usage:**
```python
table = await create(db_session, source, SourceTableCreate(
    name="customers",
    description="Customer data"
))
```

---

#### `create_column(db: AsyncSession, table: SourceTable, payload: SourceColumnCreate) -> SourceColumn`

**Purpose:** Creates a new column for a source table.

**Parameters:**
- `db` — Async database session
- `table` — Source table object
- `payload` — `SourceColumnCreate` schema

**Returns:** Created `SourceColumn` object

**Side effects:** 
- Creates column record
- Validates formula when is_calculated=True
- Invalidates table columns cache

**Usage:**
```python
column = await create_column(db_session, table, SourceColumnCreate(
    name="customer_id",
    type=ColumnType.dimension,
    data_type="integer"
))
```

---

#### `update_column(db: AsyncSession, column: SourceColumn, payload: SourceColumnUpdate) -> SourceColumn`

**Purpose:** Updates a source table column.

**Parameters:**
- `db` — Async database session
- `column` — Column object
- `payload` — `SourceColumnUpdate` schema

**Returns:** Updated `SourceColumn` object

**Side effects:** 
- Updates column record
- Validates formula constraint
- Invalidates cache

**Usage:**
```python
column = await update_column(db_session, column, SourceColumnUpdate(
    description="Updated description"
))
```

---

## 7. Configuration & Infrastructure

### Configuration Files

#### `app/core/config.py`

**Purpose:** Pydantic-based settings management with environment variable loading.

**Key Settings:**
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CACHE_TTL: int = 300
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False
    APP_TITLE: str = "LayerMap Back"
    APP_VERSION: str = "0.1.0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    REDIS_MAX_CONNECTIONS: int = 10
```

**Environment Loading:** Uses `pydantic-settings` to load from `.env` file or environment variables.

---

### Docker / Docker Compose Setup

**File:** [`docker-compose.yaml`](docker-compose.yaml:1)

**Services:**

#### PostgreSQL

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-user}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
    POSTGRES_DB: ${POSTGRES_DB:-rpi_db}
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

#### Redis

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

**Volumes:**
- `postgres_data` — Persistent PostgreSQL data

**Usage:**
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

### CI/CD Pipeline

**Status:** Not configured in this codebase.

**Recommended Setup:**
- GitHub Actions for automated testing
- Run `pytest` on every push
- Run `ruff check` for linting
- Run `ruff format --check` for formatting
- Deploy to production on main branch merge

**Example GitHub Actions workflow:**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -e .
      - run: ruff check .
      - run: ruff format --check .
      - run: pytest tests/
```

---

### Migrations Strategy

**Tool:** Alembic with SQLAlchemy 2.0 async support

**Migration Files Location:** [`alembic/versions/`](alembic/versions/)

**Key Migrations:**

| Migration ID | Description |
|--------------|-------------|
| `94aca1390145_init.py` | Initial schema (projects, sources, mapping_tables, mapping_columns, rpi_mappings) |
| `35bc1c36160b_unique_proj_name.py` | Add unique constraint on project name |
| `001_fix_measurement_type_enum.py` | Change measurement_type enum from Russian to English values |
| `5c43b21311b9_add_users_table.py` | Add users and project_members tables |
| `ba526ac7dd21_fastapi_users.py` | Add fastapi-users fields (is_active, is_superuser, is_verified) |
| `f50fdec921f8_fix_circular_fk.py` | Fix circular foreign key between sources and mapping_tables |
| `cbc528c85f8f_fix_rpi_source_column_fk.py` | Fix FK from rpi_mappings to source_columns |
| `ac218a78dc1f_fix_mapping_table_source_fk.py` | Additional FK fix |

**Migration Commands:**
```bash
# Generate new migration
alembic revision --autogenerate -m "Migration description"

# Apply migrations
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

**Alembic Configuration:** [`alembic/env.py`](alembic/env.py)

- Uses async engine with `asyncpg` driver
- Auto-generates migrations from model changes
- Compares types and server defaults

---

## 8. Testing

### How to Run Tests

**Test Framework:** pytest with pytest-asyncio

**Configuration:** [`pyproject.toml`](pyproject.toml:31)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
timeout = 60
markers = ["use_real_redis: run test against real Redis instead of mock"]
```

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_projects_api.py
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Run with timeout display:**
```bash
pytest --timeout=60 -v
```

**Run tests with real Redis:**
```bash
pytest -m use_real_redis
```

---

### Test Structure Overview

| Test File | Purpose |
|-----------|---------|
| `tests/conftest.py` | Pytest fixtures: DB session, auth client, Redis mocking |
| `tests/factories.py` | Test data factories for creating entities |
| `tests/test_health.py` | Health check endpoint tests |
| `tests/test_cache.py` | Cache layer functionality tests |
| `tests/test_errors.py` | Error handling tests |
| `tests/test_projects_api.py` | Projects CRUD API tests |
| `tests/test_sources_api.py` | Sources CRUD API tests |
| `tests/test_source_tables_api.py` | Source tables CRUD API tests |
| `tests/test_rpi_mappings_api.py` | RPI mappings CRUD API tests |
| `tests/test_contract.py` | Contract validation tests (22KB comprehensive suite) |
| `tests/test_functional_enhanced.py` | Enhanced functional tests (38KB) |
| `tests/test_security_api.py` | Security and permission tests (18KB) |
| `tests/test_performance_api.py` | Performance and load tests (17KB) |
| `tests/test_integration.py` | Integration tests (20KB) |

### Test Fixtures

**Key Fixtures in `conftest.py`:**

- `engine` — Async PostgreSQL engine
- `session_maker` — Async session factory
- `db_session` — Test database session
- `clean_tables` — Auto-cleans tables before each test
- `override_db` — Overrides DB dependency for tests
- `auto_mock_redis` — Mocks Redis by default (skip with `use_real_redis` marker)
- `authenticated` — Returns authenticated user with mocked auth
- `client` — Async HTTP client
- `auth_client` — Authenticated HTTP client

**Test Factories in `factories.py`:**

- `create_project()` — Creates test project
- `create_source()` — Creates test source
- `create_source_table()` — Creates test source table
- `create_source_column()` — Creates test source column
- `create_rpi()` — Creates test RPI mapping

---

### Coverage Notes

**Test Coverage:**
- Comprehensive API tests for all endpoints
- Permission and authorization tests
- Contract validation tests
- Performance benchmark tests
- Integration tests

**Notable Test Suites:**
- `test_contract.py` — 22,930 bytes of contract validation tests
- `test_functional_enhanced.py` — 38,695 bytes of enhanced functional tests
- `test_security_api.py` — 18,505 bytes of security tests
- `test_performance_api.py` — 17,499 bytes of performance tests
- `test_integration.py` — 20,044 bytes of integration tests

**Total Test Code:** ~140KB of test code

---

## 9. Known Limitations & TODOs

### Hard-Coded Values

| Value | Location | Should Be |
|-------|----------|-----------|
| `JWT_SECRET_KEY` | `app/core/config.py` | Loaded from environment variable |
| `CACHE_TTL` | `app/core/config.py` | Already configurable via env |
| `REDIS_MAX_CONNECTIONS` | `app/core/config.py` | Already configurable via env |
| `FAKE_PASSWORD` | `tests/conftest.py:23` | Test-only, acceptable |

### Known Issues

1. **Enum Migration Complexity**
   - MeasurementType enum was changed from Russian to English values
   - Requires complex migration with type recreation
   - See [`alembic/versions/001_fix_measurement_type_enum.py`](alembic/versions/001_fix_measurement_type_enum.py)

2. **Circular Foreign Key Resolution**
   - Multiple migrations needed to resolve circular FK between sources and mapping_tables
   - See `f50fdec921f8_fix_circular_fk.py`, `cbc528c85f8f_fix_rpi_source_column_fk.py`

3. **Cache Invalidation Patterns**
   - Pattern-based cache invalidation may miss edge cases
   - Consider adding cache versioning for critical data

4. **Password Hashing**
   - Uses bcrypt via passlib
   - Consider Argon2 for better security

### Planned Improvements

**From Code Comments:**

1. **Formula Validation**
   - Add server-side formula validation
   - Currently only checks formula is present when is_calculated=True

2. **Audit Logging**
   - No audit trail for changes to RPI mappings
   - Consider adding audit log table

3. **Bulk Operations**
   - No bulk create/update endpoints
   - Consider adding bulk import for RPI mappings

4. **Search Optimization**
   - Search uses LIKE queries
   - Consider full-text search with PostgreSQL tsvector

5. **API Versioning**
   - No API versioning strategy
   - Consider `/api/v1/` prefix for versioning

6. **Rate Limiting**
   - No rate limiting implemented
   - Consider adding rate limiting middleware

7. **Webhook Support**
   - No webhook notifications for status changes
   - Consider adding webhook system

8. **File Upload**
   - verification_file is a string path
   - Consider actual file upload with S3 or similar

### TODOs in Code

```python
# From app/services/rpi_mappings.py
# TODO: Add formula validation engine
# TODO: Add calculation preview endpoint

# From app/core/cache.py
# TODO: Add cache warming on startup
# TODO: Add cache statistics endpoint

# From tests/test_contract.py
# TODO: Add negative test cases for edge conditions
# TODO: Add concurrency tests
```

---

## 10. Glossary

### Domain Terms

| Term | Definition |
|------|------------|
| **RPI** | Russian Performance Indicators (Российские показатели эффективности) — standardized metrics used in Russian organizations |
| **RPI Mapping** | The process of mapping source data columns to standardized RPI measurements |
| **Measurement** | A specific RPI metric name (e.g., "Выручка" — Revenue) |
| **Object Field** | The target field name in the reporting object (e.g., "revenue") |
| **Ownership** | The department or team responsible for a measurement (e.g., "Финансовый департамент") |
| **Block** | A logical grouping of related RPI mappings |

### Technical Terms

| Term | Definition |
|------|------------|
| **Asyncpg** | PostgreSQL async driver for Python |
| **Alembic** | Database migration tool for SQLAlchemy |
| **Pydantic** | Data validation library using Python type annotations |
| **FastAPI-Users** | Authentication and user management for FastAPI |
| **CORS** | Cross-Origin Resource Sharing — browser security feature |
| **JWT** | JSON Web Token — stateless authentication token |
| **TTL** | Time-To-Live — cache expiration time |
| **Cascade Delete** | Automatic deletion of related records when parent is deleted |
| **Set Null** | Foreign key constraint that sets FK to NULL on parent delete |

### Enums

| Enum | Values | Description |
|------|--------|-------------|
| **ProjectStatus** | active, draft, archived | Project lifecycle status |
| **ProjectRole** | owner, editor, viewer | User permission level in project |
| **SourceType** | API, DB, FILE, STREAM | Data source type |
| **ColumnType** | dimension, metric | Column classification |
| **RPIStatus** | approved, in_review, draft | RPI mapping review status |
| **MeasurementType** | dimension, metric (nullable) | RPI measurement classification (optional) |

---

## Appendix: Quick Reference

### Common Operations

**Create a project:**
```bash
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Test"}'
```

**Register a user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass", "full_name": "User"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=user@example.com&password=securepass&grant_type=password'
```

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "database": "connected", "redis": "connected"}
```

### API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

*Document generated automatically from codebase analysis. Last updated: 2026-04-26*
