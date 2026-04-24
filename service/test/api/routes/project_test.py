from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.routes.project import get_repository
from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository
from main import app


class FakeProjectRepository(AbstractProjectRepository):
    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}

    def get_all(self) -> list[Project]:
        return list(self._projects.values())

    def get_by_id(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    def create(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    def update(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    def delete(self, project_id: UUID) -> None:
        self._projects.pop(project_id, None)


@pytest.fixture
def repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def client(repo: FakeProjectRepository) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_projects_returns_empty(client: TestClient) -> None:
    response = client.get("/projects/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects_returns_all(client: TestClient, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    response = client.get("/projects/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Arcane"


def test_get_project_returns_project(client: TestClient, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)


def test_get_project_returns_404_when_not_found(client: TestClient) -> None:
    response = client.get(f"/projects/{uuid4()}")
    assert response.status_code == 404


def test_create_project_returns_201(client: TestClient) -> None:
    body = {"name": "Arcane", "repo_path": "/repos/arcane", "default_branch": "main"}
    response = client.post("/projects/", json=body)
    assert response.status_code == 201


def test_create_project_returns_project(client: TestClient) -> None:
    body = {"name": "Arcane", "repo_path": "/repos/arcane", "default_branch": "main"}
    response = client.post("/projects/", json=body)
    data = response.json()
    assert data["name"] == "Arcane"
    assert data["repo_path"] == "/repos/arcane"
    assert data["default_branch"] == "main"
    assert "id" in data


def test_update_project_returns_updated(client: TestClient, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    body = {"name": "Arcane Updated", "repo_path": "/repos/arcane-new", "default_branch": "develop"}
    response = client.put(f"/projects/{project.id}", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Arcane Updated"
    assert data["repo_path"] == "/repos/arcane-new"
    assert data["default_branch"] == "develop"


def test_update_project_returns_404_when_not_found(client: TestClient) -> None:
    body = {"name": "Arcane", "repo_path": "/repos/arcane", "default_branch": "main"}
    response = client.put(f"/projects/{uuid4()}", json=body)
    assert response.status_code == 404


def test_delete_project_returns_204(client: TestClient, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    response = client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


def test_delete_project_returns_404_when_not_found(client: TestClient) -> None:
    response = client.delete(f"/projects/{uuid4()}")
    assert response.status_code == 404
