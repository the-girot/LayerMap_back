from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import re


class CORSMiddleware(BaseHTTPMiddleware):
    """Кастомный CORS middleware для обработки всех ответов, включая редиректы."""

    def __init__(
        self,
        app: ASGIApp,
        allow_origins: list[str] = ["*"],
        allow_methods: list[str] = ["*"],
        allow_headers: list[str] = ["*"],
        allow_credentials: bool = False,
    ):
        super().__init__(app)
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Обработка preflight-запросов (OPTIONS)
        if request.method == "OPTIONS":
            if origin and self.is_allowed(origin):
                response = Response(status_code=204)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"
                return response
            else:
                return Response(status_code=400)
        
        response = await call_next(request)

        # Добавляем CORS-заголовки ко всем ответам
        if origin and self.is_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"

        return response

    def is_allowed(self, origin: str) -> bool:
        """Проверяет, разрешен ли origin."""
        if "*" in self.allow_origins:
            return True
        for allowed in self.allow_origins:
            if origin == allowed:
                return True
            # Поддержка регулярных выражений для localhost
            if allowed.startswith("http://localhost:") or allowed.startswith("http://127.0.0.1:"):
                pattern = allowed.replace(".", r"\.").replace("*", ".*")
                if re.match(pattern, origin):
                    return True
        return False
