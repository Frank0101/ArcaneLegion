# ArcaneLegion — Claude Guidelines

## Python type annotations

All Python functions and methods must have type annotations on both parameters and return type. This includes test functions, which should be annotated `-> None`. Lambda expressions used for quick stubbing in tests are exempt.

Use `X | None` instead of `Optional[X]`. Do not import `Optional` from `typing`.

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

The domain may also contain:
- **Abstract interfaces for infra dependencies** — when the domain needs something implemented in infra (e.g. a graph executor, a repo manager, an agent runtime), the domain owns the abstract interface and infra provides the concrete implementation. See "When to use an abstract class as interface" below.
- **Orchestration classes** — classes like `RunExecutor` (coordinates repo cloning, runtime invocation, graph execution) and `RunWorker` (polling loop) that live entirely within the domain. No abstract needed for these since both caller and implementation are in the same layer.

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

### File naming within domain folders

Module files within a domain folder (`domain/<entity>/`) use generic names (`service.py`, `executor.py`, `models.py`) rather than prefixed names (`run_service.py`). The folder path already provides the domain context. Files that contain multiple unrelated classes by design (e.g. `models.py`) follow the same convention.

### Logging

Logging lives in the domain layer, not in infra. Infra components (e.g. `LangGraphManager`) are framework adapters — they have no business knowing what a "planner starting" means. The executor wraps agent actions with `_logged()` so logging happens regardless of which graph manager is wired in.

Use `logging.getLogger(__name__)` at module level.

### Strategy pattern within infra

When an infra component needs to dispatch to one of several implementations based on runtime data, use the strategy pattern entirely within infra — the domain stays unaware of it.

This is a variant of the classic Strategy pattern: rather than a single externally-selected strategy, each implementation self-declares what it can handle via `can_handle()`, and an external coordinator selects the right one at runtime. This distributes the selection logic across implementations, keeping each self-contained and the coordinator trivial.

Structure:
- The domain owns a single abstract interface (e.g. `AbstractXxx`) with the core method(s).
- In infra, a `XxxStrategy` file contains two things: an abstract strategy class (`AbstractXxxStrategy`) that extends the domain abstract and adds a `can_handle()` `@staticmethod`, and a coordinator class (`XxxStrategy`) that implements the domain abstract, holds a `list[AbstractXxxStrategy]`, and dispatches to the first strategy whose `can_handle()` returns `True`.
- Each concrete strategy inherits from `AbstractXxxStrategy` and implements both `can_handle()` and the domain method(s). These live in a dedicated subfolder in infra.
- Everything is wired at the composition root (`main.py`).

This keeps the domain interface stable. Adding a new implementation is just a new file and an extra entry in the list in `main.py`.

### Tests

Test files are co-located with the source files they test, named `<module>_test.py`.

- Route tests (`api/routes/<entity>_test.py`) override `get_service` via `app.dependency_overrides` to inject the real service backed by a fake repository, bypassing the normal dependency chain. They are E2E-style tests that cover the full request-to-response path including service logic.
- Service tests (`domain/<entity>/service_test.py`) use a fake repository. They test business logic: field generation, not-found handling, invariant preservation.
- Repository tests (`data/repositories/<entity>_test.py`) use `settings.database_url` (set to `sqlite:///:memory:` in the test environment). They test persistence correctness.
- Domain orchestration tests (`domain/<entity>/executor_test.py`, `worker_test.py`) use fake implementations of the domain's abstract interfaces. They test coordination logic: correct delegation, error propagation, argument passing.
- Infra tests (`infra/**/*_test.py`) test strategy dispatch (correct routing, error on no match) and concrete adapters (e.g. `GitHubRepoManager` subprocess call, `LangGraphManager` graph execution).

When fixtures are shared across multiple test files within the same directory scope, define them in a `conftest.py` in that directory rather than repeating them. Pytest picks these up automatically.

**Implementation conventions:**

- Prefer fake implementations (subclassing the abstract) over `unittest.mock.Mock` for domain abstractions. Fakes are explicit contracts — they fail loudly if the interface changes and make the test's intent clear. Use `unittest.mock.patch` only for genuine external calls that cannot be injected (e.g. `subprocess.run`, network calls).
- Prefix test-local helpers with `_`. Use `_FakeX` for a silent no-op that satisfies the interface, `_CapturingX` for one that records calls for later assertion. More descriptive names (e.g. `_MatchingX`, `_NonMatchingX`) are fine when they better communicate what behaviour is being set up.
- Don't test logging. It is an implementation detail — testing it ties tests to message strings rather than behaviour.

**When adding a new test, review the existing ones:**

- Look for opportunities to extract repeated setup into shared fixtures or factory helpers.
- If the same assertion holds for several inputs, use `@pytest.mark.parametrize` instead of duplicating the test — pytest's equivalent of theories in xUnit.
- Check whether a new test covers a case already handled by a more general existing test — if so, skip it.
- The goal is high coverage with a small, readable suite. Prefer fewer, well-structured tests over many narrow ones.
