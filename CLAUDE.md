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

The service is split into four layers. Each layer may only depend on layers below it, never above.

```
api/         → HTTP layer (routes, schemas)
domain/      → business logic (services, models, repository interfaces)
data/        → persistence (repository implementations, ORM models, migrations)
infra/       → framework adapters (e.g. LangGraphManager implementing AbstractGraphManager)
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

### When to use an abstract class as interface

Use an abstract class (`AbstractX`) only at a **layer boundary** — when the domain needs something whose implementation lives in a different layer (data, infra). The domain owns the abstract interface; the other layer provides the concrete implementation. Wiring happens at the composition root (`main.py`).

Do **not** create an abstract class when both the caller and the implementation live in the same layer. In that case, depend on the concrete class directly. Tests can subclass it and override the relevant methods.

Examples:
- `AbstractRunRepository` — domain interface, `RunRepository` in data/ implements it. ✓
- `AbstractGraphManager` — domain interface, `LangGraphManager` in infra/ implements it. ✓
- `RunExecutor` — no abstract needed; worker and executor are both in domain/. Tests subclass `RunExecutor` directly. ✓

### Tests

Test files are co-located with the source files they test, named `<module>_test.py`.

- Route tests (`api/routes/<entity>_test.py`) override `get_service` with a fake service backed by a fake repository. They test HTTP concerns only.
- Service tests (`domain/<entity>/service_test.py`) use a fake repository. They test business logic: field generation, not-found handling, invariant preservation.
- Repository tests (`data/repositories/<entity>_test.py`) hit a real database. They test persistence correctness.
