# ArcaneLegion — Claude Guidelines

## Python type annotations

All Python functions and methods must have type annotations on both parameters and return type. This includes test functions, which should be annotated `-> None`. Lambda expressions used for quick stubbing in tests are exempt.

Use `X | None` instead of `Optional[X]`. Do not import `Optional` from `typing`.

## Layer architecture

The service is split into four layers with the domain at the core. This draws from hexagonal architecture (Ports and Adapters) — the domain defines abstract interfaces (ports) for everything it needs from the outside, and the outer layers provide the concrete implementations (adapters). The domain depends on nothing; all other layers depend on the domain.

```
domain/  → business logic (services, models, abstract interfaces) — no dependencies
data/    → persistence (repository implementations, ORM models, migrations) — depends on domain/
infra/   → framework adapters (e.g. LangGraphManager, GitHubRepoManager) — depends on domain/
api/     → HTTP layer (routes, schemas) — depends on domain/; wires data/ and infra/
```

### API layer (`api/routes/`)

The api layer is the composition root — it is the only place where abstract interfaces are bound to concrete implementations. This happens in two places:

- **At startup** (`main.py` lifespan): infra adapters, executors, and workers are instantiated and wired together.
- **Per request** (FastAPI dependency injection): the repository is resolved for each request via:

```
route → get_service → get_repository → get_session
```

Routes are responsible for HTTP concerns only: request parsing, response serialization, status codes, and raising `HTTPException`. Business logic belongs in the service.

### Domain layer (`domain/<entity>/`)

The domain owns the business logic and defines what it needs from the outside via abstract interfaces — it never depends on who provides those things. This is the mechanism that keeps it dependency-free.

Each domain contains:
- `models.py` — pure Python dataclasses, no framework dependencies
- `repository.py` — abstract repository interface (`AbstractXRepository`), owned by the domain
- `service.py` — concrete service class, the only place business logic lives

The service depends only on the abstract repository interface, never on the concrete implementation. It is not abstract itself — there is one implementation and it lives in the domain.

The domain also defines abstract interfaces for anything it needs from infra (e.g. a graph executor, a repo manager, an agent runtime). Infra provides the concrete implementations; the domain only knows the contract. See "When to use an abstract class as interface" below.

The domain may also contain orchestration classes — classes like `RunExecutor` (coordinates repo cloning, runtime invocation, graph execution) and `RunWorker` (polling loop) that live entirely within the domain. No abstract needed for these since both caller and implementation are in the same layer.

### Data layer (`data/repositories/`)

Contains the concrete repository implementations. Data only knows about the database and the domain interfaces it implements — no other dependencies. The binding of interface → implementation happens in the api layer via FastAPI dependency injection (`get_repository`).

### Infra layer (`infra/`)

Infra contains framework adapters — concrete implementations of domain abstract interfaces that depend on external frameworks or services (e.g. `LangGraphManager`, `GitHubRepoManager`).

When an infra component needs to dispatch to one of several implementations, choose between two patterns based on where the selection logic should live.

#### Strategy pattern

Use when each adapter has an exclusive, intrinsic capability — it can handle certain inputs and cannot handle others. Selection is capability-based: each adapter self-declares what it can handle via `can_handle()`, and the coordinator picks the first matching one. The coordinator is trivial — it only routes.

Structure:
- The domain owns a single abstract interface (e.g. `AbstractXxx`) with the core method(s).
- In infra, a `XxxStrategy` file contains two things: an abstract adapter class (`AbstractXxxAdapter`) that extends the domain abstract and adds a `can_handle()` `@staticmethod`, and a coordinator class (`XxxStrategy`) that implements the domain abstract, holds a `list[AbstractXxxAdapter]`, and dispatches to the first adapter whose `can_handle()` returns `True`. Adapters are passed as a list because the set is open-ended — new implementations can be added without changing the coordinator.
- Each concrete adapter inherits from `AbstractXxxAdapter` and implements both `can_handle()` and the domain method(s). These live in a dedicated subfolder in infra.
- Everything is wired at the composition root (`main.py`).

Adding a new implementation is just a new file and an extra entry in the list in `main.py`.

#### Resolver pattern

Use when adapters are interchangeable in principle — any of them could handle any input — but the assignment is intentional: you choose which adapter to use for which input based on explicit reasoning (e.g. one model is better at planning, another at coding). There is no capability-based selection. The coordinator owns the assignment logic entirely via an internal match/switch.

The adapter abstract (`AbstractXxxAdapter`) is a plain `ABC`, not an extension of the domain abstract — the resolver may bridge between the two interfaces.

Structure:
- The domain owns a single abstract interface (e.g. `AbstractXxx`) with the core method(s).
- In infra, a `XxxResolver` file contains two things: an abstract adapter class (`AbstractXxxAdapter`, a plain `ABC`), and a coordinator class (`XxxResolver`) that implements the domain abstract, takes concrete adapters as named constructor arguments, and dispatches via an internal match/switch. Adapters are passed as named arguments rather than a list because each adapter is explicitly dispatched.
- Each concrete adapter inherits from `AbstractXxxAdapter` and implements only the execution method. These live in a dedicated subfolder in infra.
- Everything is wired at the composition root (`main.py`).

Adding a new adapter requires creating the adapter class, adding a constructor argument to the resolver, and updating the match/switch.

### When to use an abstract class as interface

Use an abstract class (`AbstractX`) when:

1. **Layer boundary** — the domain needs something whose implementation lives in a different layer (data, infra). The domain owns the abstract interface; the other layer provides the concrete implementation. Wiring happens at the composition root (`main.py`).
2. **Multiple implementations of the same contract within a layer** — when several classes must expose the same interface and may share common logic. The abstract class enforces the contract and provides a home for shared behaviour. This applies to both Strategy and Resolver adapters, with one structural difference: Strategy adapters extend the domain abstract (they are proxies — same signature, just adding `can_handle()`), while Resolver adapters are plain `ABC`s (the resolver has its own logic and the adapter signature differs from the domain abstract).

Do **not** create an abstract class for a single implementation that lives in the same layer as its caller. In that case, depend on the concrete class directly.

Examples:
- `AbstractRunRepository` — domain interface, `RunRepository` in data/ implements it. ✓ (layer boundary)
- `AbstractGraphManager` — domain interface, `LangGraphManager` in infra/ implements it. ✓ (layer boundary)
- `AbstractRepoManagerAdapter` — infra abstract for Strategy adapters; extends the domain abstract. ✓ (multiple implementations)
- `AbstractAgentRuntimeAdapter` — infra abstract for Resolver adapters; plain `ABC`. ✓ (multiple implementations)
- `RunExecutor` — no abstract needed; worker and executor are both in domain/. ✓

### File naming within domain folders

Module files within a domain folder (`domain/<entity>/`) use generic names (`service.py`, `executor.py`, `models.py`) rather than prefixed names (`run_service.py`). The folder path already provides the domain context. Files that contain multiple unrelated classes by design (e.g. `models.py`) follow the same convention.

### Logging

Logging lives in the domain layer, not in infra. Infra components (e.g. `LangGraphManager`) are framework adapters — they have no business knowing what a "planner starting" means. The executor wraps agent actions with `_logged()` so logging happens regardless of which graph manager is wired in.

Use `logging.getLogger(__name__)` at module level.

## Database migrations

Never write Alembic migration files by hand. Always generate them by running:

```bash
python -m alembic revision --autogenerate -m "short description"
```

This must be run from `service/` with `DATABASE_URL` set and the database reachable.

## Secrets handling

Never embed secrets (tokens, passwords, API keys) in URLs or subprocess command arguments — they leak into logs and tracebacks via `CalledProcessError.cmd`. Pass them via environment variables or HTTP headers instead.

When wrapping a subprocess call that uses a secret, catch `CalledProcessError` and re-raise a sanitised `RuntimeError`: use `text=True` so `e.stderr` is already a string, replace every sensitive value with `***` (both derived forms like base64 and the raw token), and use `from None` to suppress the original exception (which carries the command in `.cmd`).

```python
credentials = base64.b64encode(f"x-access-token:{self._token}".encode()).decode()
try:
    subprocess.run([
        "git", "-c", f"http.extraHeader=Authorization: Basic {credentials}",
        "clone", "--branch", branch, "--single-branch", repo_url, str(dest),
    ],
        check=True,
        capture_output=True,
        text=True,
    )
except subprocess.CalledProcessError as e:
    stderr = (
        (e.stderr or "")
        .strip()
        .replace(credentials, "***")
        .replace(self._token, "***")
    )
    raise RuntimeError(f"git clone failed (exit {e.returncode}): {stderr}") from None
```

## Tests

Test files are co-located with the source files they test, named `<module>_test.py`.

- Route tests (`api/routes/<entity>_test.py`) override `get_service` via `app.dependency_overrides` to inject the real service backed by a fake repository, bypassing the normal dependency chain. They are E2E-style tests that cover the full request-to-response path including service logic.
- Service tests (`domain/<entity>/service_test.py`) use a fake repository. They test business logic: field generation, not-found handling, invariant preservation.
- Repository tests (`data/repositories/<entity>_test.py`) use `settings.database_url` (set to `sqlite:///:memory:` in the test environment). They test persistence correctness.
- Domain orchestration tests (`domain/<entity>/executor_test.py`, `worker_test.py`) use fake implementations of the domain's abstract interfaces. They test coordination logic: correct delegation, error propagation, argument passing.
- Infra tests (`infra/**/*_test.py`) test strategy dispatch (correct routing, error on no match), resolver dispatch (correct adapter selection, input mapping) and concrete adapters (e.g. `GitHubRepoManager` subprocess call, `LangGraphManager` graph execution).

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
