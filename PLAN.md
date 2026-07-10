# Recipe & Dinner-Invite App — Plan & Gap Tracker

Vision: a simple recipe-sharing site where people can post recipes, like them,
and invite close friends over to cook/eat. Functionality first — styling and
optimization come later.

_Last reviewed: 2026-07-09_

## Current State

Django 5.2 + Postgres, custom user model. Four apps:

- **apps/accounts** — custom `User` (adds `cooking_technologies`), `Friendship` model
  (one-directional, unilateral — like a personal contacts list, no accept/decline step),
  register/friend list/add/remove views.
- **apps/recipes** — `Recipe` (title, instructions, servings, ingredients, dietary tags,
  cooking tech, picture, embedding), `RecipeLike`, `RecipeComment`, `RecipeMade` ("I made
  this" photo/note), `RecipeCollection` models; create/edit/delete/list/detail views;
  search with any/all ingredient matching, fuzzy title search (Postgres `pg_trgm`),
  dietary/cooking-tech filters, pantry "closest match" ranking, and a sort control; like
  toggle endpoint. `ingredients`/`cooking_technologies`/`dietary_tags` are all fixed
  vocabularies defined in `apps/recipes/constants.py` (not free text).
- **apps/social** — `DinnerEvent`/`EventDish` (potluck-style claimable dishes, `null`
  `claimed_by` = up for grabs)/`EventInvite` (per-guest RSVP) models; create/list/detail/
  respond/claim/`.ics`-export views. Any registered user can be invited — the
  friend-flagging in `event_create` is a UI convenience, not an access gate.
- **apps/recommendations** — `RecipeEmbeddingService` (cosine-similarity over a
  ingredient/cooking-tech/time embedding) powers `recipe_detail`'s "Similar recipes"
  panel; `FriendRecommendationService` (direct aggregate of friends' `RecipeLike`s, no
  ML) powers `recipe_list`'s "Recommended by your friends" section. Both were chosen
  specifically to avoid the cold-start problem — see "Recommendations" below for what's
  deferred.

Templates are bare (no styling, by design): base, recipe list/detail/create/edit,
collections, login/register, friends, dinner-event create/list/detail.

Business logic that a non-web client also needs lives in each app's `services.py`
(`RecipeService`/`CollectionService`/`RecipeSearchService` in `apps/recipes`,
`EventService` in `apps/social`, `FriendshipService` in `apps/accounts`) — both the
template views and the API views below call the same service functions rather than
duplicating logic per client.

A DRF API layer (`api/` package + `apps/*/serializers.py`+`api_views.py`+`api_urls.py`,
mounted at `/api/v1/`) exposes this same functionality as JSON for a future mobile
client — see "API layer" below. `ios/` holds the directory skeleton for a future
Swift/Xcode client (no Xcode project yet).

Test suite: pytest + pytest-django, 108 tests — see "Testing" below for how to run it.

## Known gaps / pending work

- **No user-facing profile / friend browsing** — no way to view another user's profile.
- **No dinner-event notifications** — a recipient only finds out about an invite by
  visiting `/social/events/` themselves; no in-app badge or email.
- **No reminder emails** as an event date approaches — would need a scheduled task
  (cron/Celery), a bigger infra lift than anything built so far.
- **No handling of past-dated dinner events** — an event whose date has passed just sits
  with whatever RSVP status it had forever.
- **Friendship has no reverse-lookup** — only the forward direction (`user1`, i.e. "my
  friends") is surfaced; there's no "who has added me as a friend" view.
- **"Host a Dinner" doesn't preselect a recipe** — the link from `recipe_detail` goes to
  the generic `event_create` form rather than prefilling that recipe as a dish; would
  need a query-param prefill (UI polish, not attempted).
- **Pre-existing recipes have placeholder content** — rows created before `title`/
  `instructions` existed got a one-off migration default (`"Untitled"` /
  `"No instructions yet."`); fine for a dev DB, needs a real backfill before real users
  see this.

## API layer — added 2026-07-09

Groundwork for an eventual iOS app (Option A from the earlier mobile-architecture
discussion: Django stays at repo root, `api/` is a new top-level package, `ios/` is a
sibling directory for a future separate Xcode project — no app built yet).

- **Auth**: DRF's built-in `TokenAuthentication` (`rest_framework.authtoken`), not JWT —
  zero extra dependency beyond DRF itself, matching this repo's existing bias toward
  fewer dependencies. `POST /api/v1/auth/token/` (login) and
  `POST /api/v1/accounts/register/` both return `{"token": "..."}`. Upgrading to
  `djangorestframework-simplejwt` later (for token expiry/refresh) is a contained change
  if it's ever needed — not required to make the API usable today.
- **Structure**: mirrors the existing per-domain-app convention (each app already owns
  its `models.py`/`views.py`/`services.py`/`admin.py`/`tests/`) — the API layer gets the
  same treatment (`serializers.py`, `api_views.py`, `api_urls.py` per app) rather than a
  separate centralized structure. The new top-level `api/` package holds only
  cross-cutting routing (`api/urls.py`, mounted at `/api/v1/`) and the schema.
- **Coverage**: recipes (CRUD, search incl. `match_mode`/fuzzy title/dietary
  tags/sort, like toggle, comments, "made this", popular, collections + toggle-recipe,
  vocabulary), social (dinner events — list/create/retrieve only, no edit/delete, since
  the web app has none either; dish claim, RSVP respond, `.ics` export, invited-events
  list), accounts (register, friend list/add/remove). Permission/ownership rules mirror
  the web views exactly (e.g. `recipe_detail`-equivalent is `AllowAny`, edit/delete is
  creator-only and 404s — not 403s — for everyone else, event retrieval 404s for anyone
  who isn't the host or an invited guest).
- **OpenAPI schema**: generated via `drf-spectacular` and committed at `api/schema.yaml`
  — regenerate with `python manage.py spectacular --file api/schema.yaml` whenever a
  serializer or API view changes shape. Every endpoint (including the handful of plain
  `APIView`s that aren't naturally `ModelSerializer`-shaped — register, friend add/remove,
  vocabulary, dish claim) has an explicit `@extend_schema`/`extend_schema_field`
  annotation so schema generation runs with **zero warnings or errors**, not just a
  graceful partial fallback.
- **Tests**: `apps/*/tests/test_api.py` (28 tests), using a new `api_client`/
  `api_client_as` fixture pair in `conftest.py` wrapping `rest_framework.test.APIClient`
  with real token auth (not mocked).

**Not built (deliberately, not forgotten):**
- The actual iOS Xcode project — only the `ios/` directory skeleton + READMEs exist.
- Pagination/throttling customization — DRF defaults apply; fine at current data volume,
  same "optimize when it's a measured problem" stance as everywhere else in this project.
- A "prefill this recipe as a dish" query-param shortcut from `recipe_detail` into
  `event_create`'s API equivalent (already noted as a web-side gap above too).

## Recommendations — current state & further work

Both live recommendation features were chosen specifically to avoid the cold-start
problem: they work from day one with zero interaction history.

- **"Similar recipes" panel** (`RecipeEmbeddingService.find_similar_recipes`, on
  `recipe_detail`): content-based cosine similarity, brute-force over all recipes in
  Python. Ties (common given the small mostly-binary embedding) are broken by
  `like_count` then `created_at`. Recipes with a mismatched/empty embedding (e.g.
  created via `/admin/`, bypassing the normal embedding computation) are skipped rather
  than crashing.
- **"Recommended by your friends"** (`FriendRecommendationService`, on `recipe_list`):
  a direct aggregate of `RecipeLike` rows from the user's `Friendship` list, ranked by
  number of friends who liked each recipe — deliberately not collaborative filtering,
  since with a small friend graph CF similarity scores would just be noise.

**Further work, not yet built:**

- **Real collaborative filtering** once there's a good number of users/likes: a sparse
  user×recipe interaction matrix from `RecipeLike` (`scipy.sparse`/`sklearn`, already a
  dependency), item-item or user-user CF. Revisit once there's enough like volume for
  this to actually beat the current friends-aggregate baseline.
- **Personalized "recommended for you"** via a user taste-vector: mean (or
  recency-weighted mean) of the embeddings of recipes a user has liked, cosine-ranked
  against all recipes. Cold start for a user with zero likes: fall back to
  `popular_recipes` or a random sample.
- **Exploration/discovery slot**: replace one slot in a ranked list (epsilon-greedy,
  ~10-20%) with a random recipe the user hasn't liked, so recommendations don't
  calcify into only near-duplicates of what's already been liked.
- **Move off brute-force cosine similarity** once it's a measured bottleneck (recipe
  count in the thousands+): precomputed/indexed vector search (pgvector, FAISS). Don't
  do this preemptively.
- **TF-IDF-style ingredient weighting**: the current one-hot ingredient encoding treats
  all 20 ingredients as equally distinctive; down-weighting ubiquitous ones and
  up-weighting rare ones would sharpen similarity. Worth doing if the "Similar recipes"
  panel ever feels like it's not surfacing meaningfully different recipes.

## Testing

Runner: **pytest + pytest-django** (not Django's built-in `manage.py test`). Config in
`pytest.ini` at repo root. Shared fixtures (`user`, `user_factory`, `recipe_factory` —
the latter computes a real embedding via `RecipeEmbeddingService`; `api_client`/
`api_client_as` — token-authenticated `rest_framework.test.APIClient` instances) live in
a root `conftest.py`. Tests live alongside each app in `apps/<app>/tests/`.

**One-time local setup requirement:** the app's Postgres role (`edwin`, created by
`startup.sh`) needs `CREATEDB` so pytest-django can create `test_recipe_db`
(`ALTER USER edwin CREATEDB;` — `startup.sh` already does this for fresh installs).

**Run it:**
- `pytest` — full suite (108 tests as of 2026-07-09, all passing).
- `pytest apps/recipes` — just one app.
- `pytest -k SomeClassName` — keyword filter, matched against test IDs including the
  `TestSomething` class name (e.g. `-k FriendAdd`, not `-k friend_add` — class names are
  CamelCase).

**Lesson learned (2026-07-05):** every `apps/<app>/` package needs its own `__init__.py`
(not just `apps/<app>/tests/`) — without it, same-named test modules across apps (e.g.
two different `test_views.py`) can silently collide and get skipped, while the run still
reports a clean "N passed." A green full-suite run isn't proof the tests you think are
running actually are — spot-check with a targeted `-k`/file-path run when in doubt,
especially after touching pytest config.
