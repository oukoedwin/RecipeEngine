# RecipeEngine iOS

Reserved for a future native iOS client (Swift/SwiftUI). No Xcode project exists here
yet — this is the directory skeleton so the intended structure exists ahead of that work.

## The contract

The backend's API lives at `/api/v1/` (see the Django project's `api/` package). Its
OpenAPI schema is committed at [`../api/schema.yaml`](../api/schema.yaml) — regenerate
it from the backend with `python manage.py spectacular --file api/schema.yaml` whenever
a serializer or API view changes shape. Treat that file as the source of truth for
request/response shapes rather than reading Django serializer source directly.

Auth: `POST /api/v1/auth/token/` (username/password) or `POST /api/v1/accounts/register/`
both return `{"token": "..."}` — send it back as `Authorization: Token <token>` on every
subsequent request (DRF `TokenAuthentication`).

Interactive docs (once the backend is running): `/api/v1/docs/`.

## Intended structure

```
RecipeEngine/
├── App/            — app entry point, root navigation
├── Features/
│   ├── Recipes/        — recipe list/detail/create, comments, "made this", collections
│   ├── DinnerEvents/   — event list/detail/create, dish claiming, RSVP, calendar export
│   ├── Friends/        — friend list/add/remove
│   └── Auth/           — login/register, token storage
├── Networking/      — API client, one function per api/schema.yaml operation
├── Models/          — Codable structs mirroring api/schema.yaml component schemas
└── Resources/       — Assets.xcassets, Info.plist

RecipeEngineTests/
```

## Why this shape

Mirrors the backend's own per-domain-app convention (each Django app owns its
`models.py`/`views.py`/`serializers.py`; each Swift feature folder owns its views/view
models for one domain) rather than organizing by technical layer only.
