from httpx import AsyncClient


async def create_project(client: AsyncClient, name: str = "Test Project") -> int:
    response = await client.post(
        "/projects",
        json={"name": name, "description": "Desc", "status": "active"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
