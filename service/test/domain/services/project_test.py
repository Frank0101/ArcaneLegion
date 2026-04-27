from uuid import UUID, uuid4

import pytest

from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository
from domain.project.service import ProjectService


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
def service(repo: FakeProjectRepository) -> ProjectService:
    return ProjectService(repo)


def test_get_all_returns_empty(service: ProjectService) -> None:
    assert service.get_all() == []


def test_get_all_returns_all(service: ProjectService, repo: FakeProjectRepository) -> None:
    repo.create(Project(id=uuid4(), name="A", repo_path="/a", default_branch="main"))
    repo.create(Project(id=uuid4(), name="B", repo_path="/b", default_branch="main"))
    assert len(service.get_all()) == 2


def test_get_by_id_returns_project(service: ProjectService, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    assert service.get_by_id(project.id) == project


def test_get_by_id_returns_none_when_not_found(service: ProjectService) -> None:
    assert service.get_by_id(uuid4()) is None


def test_create_assigns_id(service: ProjectService) -> None:
    project = service.create(name="Arcane", repo_path="/repos/arcane", default_branch="main")
    assert project.id is not None


def test_create_sets_provided_fields(service: ProjectService) -> None:
    project = service.create(name="Arcane", repo_path="/repos/arcane", default_branch="main")
    assert project.name == "Arcane"
    assert project.repo_path == "/repos/arcane"
    assert project.default_branch == "main"


def test_create_ids_are_unique(service: ProjectService) -> None:
    p1 = service.create(name="A", repo_path="/a", default_branch="main")
    p2 = service.create(name="B", repo_path="/b", default_branch="main")
    assert p1.id != p2.id


def test_update_returns_updated_project(service: ProjectService, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Old", repo_path="/old", default_branch="main")
    repo.create(project)
    updated = service.update(Project(id=project.id, name="New", repo_path="/new", default_branch="develop"))
    assert updated is not None
    assert updated.name == "New"
    assert updated.repo_path == "/new"
    assert updated.default_branch == "develop"


def test_update_returns_none_when_not_found(service: ProjectService) -> None:
    assert service.update(Project(id=uuid4(), name="X", repo_path="/x", default_branch="main")) is None


def test_delete_returns_true_when_deleted(service: ProjectService, repo: FakeProjectRepository) -> None:
    project = Project(id=uuid4(), name="Arcane", repo_path="/repos/arcane", default_branch="main")
    repo.create(project)
    assert service.delete(project.id) is True
    assert repo.get_by_id(project.id) is None


def test_delete_returns_false_when_not_found(service: ProjectService) -> None:
    assert service.delete(uuid4()) is False
