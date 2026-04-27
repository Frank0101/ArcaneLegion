# ArcaneLegion — Claude Guidelines

## Python type annotations

All Python functions and methods must have type annotations on both parameters and return type. This includes test functions, which should be annotated `-> None`.

## Database migrations

Never write Alembic migration files by hand. Always generate them by running:

```bash
python -m alembic revision --autogenerate -m "short description"
```

This must be run from `service/` with `DATABASE_URL` set and the database reachable.

## Layer architecture

The service is split into three layers. Each layer may only depend on layers below it, never above.

```
api/         → HTTP layer (routes, schemas)
domain/      → business logic (services, models, repository interfaces)
data/        → persistence (repository implementations, ORM models, migrations)
```

### Domain layer (`domain/<entity>/`)

Each domain contains:
- `models.py` — pure Python dataclasses, no framework dependencies
- `repository.py` — abstract repository interface (`AbstractXRepository`), owned by the domain
- `service.py` — concrete service class, the only place business logic lives

The service depends only on the abstract repository interface, never on the concrete implementation. It is not abstract itself — there is one implementation and it lives in the domain.

### Data layer (`data/repositories/`)

Contains the concrete repository implementations. These implement the abstract interfaces defined in the domain. The binding of interface → implementation is done in the API layer via FastAPI dependency injection (`get_repository`).

### API layer (`api/routes/`)

Routes depend on the service, not the repository directly. The dependency chain is:

```
route → get_service → get_repository → get_session
```

`get_repository` is the IoC resolution point where the abstract interface is bound to the concrete implementation.

Routes are responsible for HTTP concerns only: request parsing, response serialization, status codes, and raising `HTTPException`. Business logic belongs in the service.

### Tests

- Route tests (`test/api/routes/`) override `get_service` with a fake service backed by a fake repository. They test HTTP concerns only.
- Service tests (`test/domain/<entity>/`) use a fake repository. They test business logic: field generation, not-found handling, invariant preservation.
- Repository tests (`test/data/repositories/`) hit a real database. They test persistence correctness.
