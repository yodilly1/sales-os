# Database Migrations

This directory contains database migration files for Sales OS.

## Migration Naming Convention

Migrations should follow this naming pattern:
```
YYYYMMDDHHMMSS_description.sql
```

Example: `20241122120000_add_pipeline_stages.sql`

## Running Migrations

### Development
Migrations in `init/` run automatically when the PostgreSQL container starts for the first time.

For subsequent migrations, use the migration tool of your choice:
- [Alembic](https://alembic.sqlalchemy.org/) (recommended for Python/FastAPI)
- [golang-migrate](https://github.com/golang-migrate/migrate)
- [Flyway](https://flywaydb.org/)

### Production
```bash
# Using Alembic (example)
cd backend
alembic upgrade head

# Using migrate CLI (example)
migrate -path ./infra/db/migrations -database $DATABASE_URL up
```

## Best Practices

1. **Always test migrations locally** before applying to staging/production
2. **Make migrations reversible** when possible
3. **Never modify existing migrations** that have been applied to production
4. **Use transactions** for data integrity
5. **Add appropriate indexes** for new columns used in queries
6. **Document breaking changes** in migration comments
