# FrameRate backend (Flask)

## Run it (Windows Command Prompt)

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask db upgrade
python run.py
```

Then open http://127.0.0.1:5000/api/health. You should see `"status": "ok"` and `"database": "ok"`.

- `copy .env.example .env` is only needed once. Put your own values in `.env` (it is never committed).
- `flask db upgrade` creates the local database in `backend/instance/` (never committed).
- Run the tests with `pytest` from the `backend` folder.
- To start over with an empty database: stop the server, delete `backend\instance\framerate.db`, run `flask db upgrade`.
- The old `backend/app.py` is replaced by `run.py`. The new command is `python run.py`.

## Folder map

```
backend/
  run.py                  starts the server (python run.py)
  .flaskenv               tells the flask command where the app is
  pytest.ini              test settings
  app/
    __init__.py           create_app(): wires everything together
    config.py             settings read from .env
    extensions.py         db and migrate objects, SQLite foreign-key switch
    models/               one file per table (see docs/database-schema.md)
    blueprints/           one file per feature's routes
    utils/                security helpers and validators     (Dev 4)
    services/             ranking and recommendation logic    (Dev 5)
  migrations/             database change history (commit these files)
  tests/                  pytest tests
```

## Who edits what (keeps merges clean)

| Area | Owner | Files |
|---|---|---|
| App setup, models, auth, TMDB wrapper | Dev 3 | `app/__init__.py`, `config.py`, `extensions.py`, `models/`, `blueprints/auth.py`, `blueprints/movies.py` |
| Security, validation, error handling, logging, preferences | Dev 4 | `app/utils/`, `blueprints/preferences.py` (error-handler and logging files: Dev 4 decides the names) |
| Ranking, ratings, reviews, watchlist | Dev 5 | `app/services/`, `blueprints/ratings.py`, `reviews.py`, `watchlist.py` |

Every blueprint already exists as an empty file, so you add routes without touching `__init__.py`.
Dev 4 only needs to add two lines in `app/__init__.py`, at the comment marked `SEC-02`.

## Changing the database

1. Add or edit a model in `app/models/`. A new model file must also be imported in `app/models/__init__.py`.
2. Run `flask db migrate -m "short description"`. A new file appears in `migrations/versions/`.
3. **Open that file and read it.** Alembic misses some things (for example, expression indexes on SQLite).
4. Run `flask db upgrade`, then `pytest`, then commit the model change **and** the migration file together.

Rules:
- Never edit a migration that has been merged. Add a new one.
- If Git or Flask complains about "multiple heads" (two people made a migration at the same time), run
  `flask db merge heads -m "merge heads"` and commit the result.
- After pulling someone else's migration, run `flask db upgrade`.

## Decisions made in the schema

- **Ratings are whole stars, 1 to 5.** The frontend's star component sets whole numbers. Half stars would need a new migration.
- **Watchlist statuses:** `plan`, `watched`, `on_hold`, `dropped` (the four statuses in the DATA-04 ticket).
- **Movies table is a cache** of TMDB data. Update its rows, never delete them: ratings and watchlist entries point to it. A movie must be saved in this table before it can be rated or added to a watchlist.
- **Ratings have a status** (`active`, `quarantined`, `removed`). Rankings must count `active` ratings only.
- **Usernames and emails are unique ignoring case.**