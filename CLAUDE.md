# ArcaneLegion — Claude Guidelines

## Python type annotations

All Python functions and methods must have type annotations on both parameters and return type. This includes test functions, which should be annotated `-> None`.

## Database migrations

Never write Alembic migration files by hand. Always generate them by running:

```bash
python -m alembic revision --autogenerate -m "short description"
```

This must be run from `service/` with `DATABASE_URL` set and the database reachable.
