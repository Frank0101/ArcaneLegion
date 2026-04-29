from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from data.repositories.project import ProjectRepository
from domain.project.models import Project


@pytest.fixture
def repo(session: Session) -> ProjectRepository:
    return ProjectRepository(session)


def _make_project(
        project_id: UUID | None = None,
        name: str = "Arcane",
        repo_path: str = "/repos/arcane",
        default_branch: str = "main",
) -> Project:
    return Project(
        id=project_id or uuid4(),
        name=name,
        repo_path=repo_path,
        default_branch=default_branch,
    )


def test_create_and_get_by_id(repo: ProjectRepository) -> None:
    project = _make_project()

    created = repo.create(project)
    result = repo.get_by_id(project.id)

    assert created == project
    assert result == project


def test_get_by_id_returns_none_when_not_found(repo: ProjectRepository) -> None:
    assert repo.get_by_id(uuid4()) is None


def test_get_all_returns_all_projects(repo: ProjectRepository) -> None:
    first = _make_project(name="Arcane")
    second = _make_project(name="Legion", repo_path="/repos/legion", default_branch="develop")
    repo.create(first)
    repo.create(second)

    results = repo.get_all()

    assert {project.id for project in results} == {first.id, second.id}


def test_update_returns_updated_project(repo: ProjectRepository) -> None:
    project = _make_project()
    repo.create(project)
    updated = Project(
        id=project.id,
        name="Arcane Updated",
        repo_path="/repos/arcane-updated",
        default_branch="develop",
    )

    result = repo.update(updated)

    assert result == updated
    assert repo.get_by_id(project.id) == updated


def test_update_raises_when_not_found(repo: ProjectRepository) -> None:
    project = _make_project()

    with pytest.raises(ValueError, match=f"Project {project.id} not found"):
        repo.update(project)


def test_delete_removes_project(repo: ProjectRepository) -> None:
    project = _make_project()
    repo.create(project)

    repo.delete(project.id)

    assert repo.get_by_id(project.id) is None


def test_delete_ignores_missing_project(repo: ProjectRepository) -> None:
    repo.delete(uuid4())
