# Recipe & Dinner-Invite App — Plan & Gap Tracker

Vision: a simple recipe-sharing site where people can post recipes, like them,
and invite close friends over to cook/eat. Functionality first — styling and
optimization come later.

_Last reviewed: 2026-07-05_

## Current State

Django 5.2 + Postgres, custom user model. Four apps:

- **apps/accounts** — custom `User` (adds `cooking_technologies`), `Friendship` model, register view.
- **apps/recipes** — `Recipe` (title, instructions, servings, ingredients, dietary tags,
  cooking tech, picture, embedding), `RecipeLike`, `RecipeComment`, `RecipeMade`,
  `RecipeCollection` models; create/edit/delete/list/detail views; ingredient/time/tech/
  dietary/fuzzy-title search with any/all matching, pantry "closest match" ranking, and
  sort control; like toggle endpoint.
- **apps/social** — `DinnerEvent`/`EventDish` (potluck-style claimable dishes)/`EventInvite`
  models; create/list/detail/respond/claim/`.ics`-export views.
- **apps/recommendations** — cosine-similarity embedding service (numpy/sklearn) wired into
  `recipe_detail`'s "Similar recipes" panel, plus `FriendRecommendationService` wired into
  `recipe_list`'s "Recommended by your friends" section.

Templates are bare (no styling, as expected): base, recipe list/detail/create/edit,
collections, login/register, friends, dinner-event create/list/detail.

## Bugs — fixed 2026-07-04

1. ~~**Login redirect 404s.**~~ Added `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL = 'recipe_list'` to `recipe/settings.py`.
2. ~~**Logout is broken.**~~ `templates/base.html` now renders logout as a `<form method="post">` + button instead of a GET link, matching Django 5's POST-only `LogoutView`.
3. ~~**Invites use the wrong User model.**~~ `apps/social/models.py` no longer imports the stock `django.contrib.auth.models.User` (it was unused there anyway). `apps/social/views.py` now uses `get_user_model()` so the recipient picker and lookups hit the real `accounts.User` table.
4. ~~**`popular_recipes` view is dead/broken.**~~ Added the missing `from django.db.models import Count` import, wired `popular_recipes` into `apps/recipes/urls.py` (`/recipe/popular/`), and added `templates/recipes/popular.html` so it's actually reachable.
5. ~~**Cache backend will error on first use.**~~ Switched `CACHES` from `django.core.cache.backends.redis.RedisCache` (package not installed) to Django's built-in `locmem.LocMemCache` — no extra infra needed for dev. Revisit if/when a real shared cache is needed in production.
6. ~~**Like button never shows "Unlike".**~~ `recipe_detail` view now computes and passes `user_has_liked`; the template checks that instead of the invalid `recipe.recipelike_set.all.user` expression, and the JS handler updates the button label (not just the count) after a toggle.
7. ~~**gunicorn.service has the wrong working directory.**~~ `WorkingDirectory` now points at the repo root (where `manage.py` lives) instead of the inner `recipe/` settings package.

## Feature gaps vs. the stated vision

- ~~**Friendship is unused.**~~ — fixed 2026-07-04. Friendship is one-directional and unilateral (like a personal contacts list, no accept/decline step — matches the model's shape, which has no `status` field): `apps/accounts` now has `friend_list`/`friend_add`/`friend_remove` views + `templates/accounts/friend_list.html`, reachable via a "Friends" nav link. The original `invite_create` was changed from a single `<select>` to a multi-select checkbox list with friends flagged + a "Select all friends" button — this same friend-flagging logic now lives in `event_create` (Plan 3 superseded `invite_create` entirely, see backlog below).
- ~~**No Django admin registrations**~~ — fixed 2026-07-04: added `admin.py` in `apps/accounts` (`User` via a `UserAdmin` subclass that also shows `cooking_technologies`, plus `Friendship`), `apps/recipes` (`Recipe`, `RecipeLike`, and later `RecipeComment`/`RecipeMade`/`RecipeCollection`), and `apps/social` (originally `Invite`, now `DinnerEvent`/`EventDish`/`EventInvite` after Plan 3).
- ~~**No tests** anywhere~~ — fixed 2026-07-04, see "Testing" section below.
- ~~**Recommendations service isn't wired up.**~~ — partially fixed 2026-07-04: see "Recommendations" section below for what's live vs. deferred.
- ~~**Ingredient embedding is disconnected from real data.**~~ — fixed 2026-07-04. Decision: keep a small **fixed, controlled ingredient vocabulary** (20 common ingredients) rather than free text — this matches what `notes.md` originally scoped ("Initially account for 20 ingredients") and is far simpler than building fuzzy/NLP ingredient normalization right now. Added `apps/recipes/constants.py` with `INGREDIENT_CHOICES` (20 items) and `COOKING_TECHNOLOGY_CHOICES`, shared by both `RecipeForm`/`RecipeSearchForm` (now `CheckboxSelectMultiple` instead of free-text `Textarea`/`TextInput`) and `RecipeEmbeddingService` (`INGREDIENTS_LIST`/`COOKING_TECH` now just alias the same constants instead of placeholder `Ing_0..Ing_19` names). A recipe's `ingredients` JSON list is now always drawn from the same 20 names the embedding encodes, so the vector is finally meaningful. Trade-off accepted for now: any recipe created before this change with free-text ingredients won't have valid checkbox state when edited (its stored strings likely won't match the fixed vocabulary) — fine for a dev DB, but worth a data cleanup pass before this goes anywhere near real users. Expanding past 20 ingredients still means editing `INGREDIENT_CHOICES` by hand, per the original scope note.
- ~~**Search is OR-only.**~~ — fixed 2026-07-05 as part of the Search plan (Plan 2, see backlog below): `RecipeSearchService.search_recipes` now takes a `match_mode` (`'any'`/`'all'`).
- ~~**No recipe edit/delete.**~~ — fixed 2026-07-04: added `recipe_edit`/`recipe_delete` views (both restricted to the recipe's creator), routes, and a `templates/recipes/edit.html` page with a delete button; `recipe_detail.html` now shows an "Edit" link to the creator. `RecipeForm` also now correctly repopulates the ingredients textarea from the stored list when editing.
- **No user-facing profile / friend browsing** — no way to see other users' profiles distinct from the dinner-events list. Still open.
- **No dinner-event notifications** — recipient only finds out by visiting `/social/events/` themselves; no in-app badge or email. Still open (explicitly deferred again in Plan 3, see backlog below).
- ~~**Invite is 1 recipe : 1 recipient.**~~ — fixed 2026-07-04 as part of the Friends work, then superseded entirely 2026-07-05: the whole `Invite` model was replaced by `DinnerEvent`/`EventDish`/`EventInvite`, which supports many dishes and many guests per event natively (see Plan 3 in the backlog below).
- **No handling of past-dated dinner events** — an event whose date has passed just sits with whatever RSVP status it had forever; still open (carried over from the old "past-dated invites" gap, now applies to `DinnerEvent`).
- ~~**No fuzzy/approximate matching**~~ — fixed 2026-07-05 as part of the Search plan (Plan 2): fuzzy title search via Postgres `pg_trgm`/`TrigramSimilarity`.

## Feature backlog (2026-07-05)

Ideas from a functionality brainstorm (web-researched: schema.org `Recipe`, dinner/potluck
RSVP apps like RSVPify/Potluck.us/PartyLabz/Partiful, Django+Postgres trigram fuzzy search,
pantry-style ingredient-match ranking used by tools like SuperCook/RecipeRadar).
Recommendation-related ideas are explicitly **not** part of this backlog — see the
"Recommendations" section above, which already tracks that as deferred. The three areas
below are being actively worked on, each independently implementable, and each ignoring
UI/UX by design (styling is a separate, later concern per the project's stated vision).

### Recipe content (Plan 1 — done 2026-07-05)
- ~~`title` field~~ — added (`CharField`, required). Also unblocked fuzzy search (Plan 2).
- ~~`instructions` field~~ — added (`TextField`, required, free text — steps separated
  by the user, no per-step model; schema.org's `HowToStep` object model is a possible
  future upgrade but not needed for v1).
- ~~`servings` field~~ — added (`PositiveIntegerField`, default 4).
- ~~`dietary_tags`~~ — added as a fixed vocabulary (`DIETARY_TAG_CHOICES` in
  `apps/recipes/constants.py`: Vegetarian, Vegan, Gluten-Free, Dairy-Free, Nut-Free,
  Halal, Kosher), same `CheckboxSelectMultiple` pattern as `cooking_technologies`.
- ~~`RecipeComment` model~~ — added, with `recipe_comment_add` view (POST-only,
  `login_required`) and a comment list + form on `recipe_detail`.
- ~~`RecipeMade` model~~ ("I made this") — added (photo + note, by someone other than
  the creator), with `recipe_made_add` view and a "Made by others" section on
  `recipe_detail`. Closes the loop on `notes.md`'s "add photos of finished food" from
  the guest's side.
- ~~`RecipeCollection` model~~ — added, with `collection_list`/`collection_create`/
  `collection_detail`/`collection_toggle_recipe` views, all scoped to the owning user.
- All new models registered in `apps/recipes/admin.py`; `conftest.py`'s `recipe_factory`
  extended with `title`/`instructions`/`servings`/`dietary_tags` defaults; 18 new tests
  added across `apps/recipes/tests/test_models.py`, `test_forms.py`, `test_views.py`.
- **Caveat carried over:** pre-existing dev-DB rows got placeholder `title`="Untitled"/
  `instructions`="No instructions yet." via the migration's one-off default — fine for
  dev data, would need a real backfill before any real users hit this.

### Search (Plan 2 — done 2026-07-05)
- ~~Fix the long-standing `# TODO` in `RecipeSearchService` for `match_mode` any/all~~ —
  added a `match_mode` param (`'any'`/`'all'`); `'all'` uses Postgres JSONField
  `contains` on a *list* value (`ingredients__contains=['Chicken','Rice']`), which checks
  containment of the whole sublist in one query — no OR-loop needed.
- ~~Pantry-style "closest match" ranking~~ — added
  `RecipeSearchService.rank_by_missing_ingredients(available_ingredients)`, annotates each
  recipe with `.missing_ingredients` and sorts by fewest-missing then `like_count`. Wired
  into `search_recipes` via a `sort='closest_match'` option, and into `list.html` (shows a
  "Missing: ..." line when present).
- ~~Fuzzy title search~~ — added via Postgres `pg_trgm` (new migration
  `0003_trigram_extension.py` using `TrigramExtension()`) and
  `django.contrib.postgres.search.TrigramSimilarity` on `title`, threshold 0.3 (Postgres'
  own default for the `%` operator). Finally gives `notes.md`'s long-standing "fuzzy/
  approximate searching" task a concrete target.
- ~~Dietary tag filter~~ — added, same `Q(dietary_tags__contains=tag)` OR-loop pattern
  already used for `cooking_technologies`.
- ~~Explicit sort control~~ — added (`relevance`/`newest`/`quickest`/`closest_match`) as
  a `RecipeSearchForm` field, replacing the previously-hardcoded `-like_count, -created_at`.
- 8 new tests in `apps/recipes/tests/test_services.py` covering all of the above.

### Social / dinner coordination (Plan 3 — done 2026-07-05; replaced `Invite`)
- ~~Multi-dish `DinnerEvent` model + `EventDish` + `EventInvite`~~ — `Invite` (sender,
  recipient, single recipe, date/time, status) fully replaced by `DinnerEvent` (host,
  title, date, time, location) + `EventDish` (recipe, nullable `claimed_by` — potluck-style,
  null means "up for grabs") + `EventInvite` (per-guest RSVP, `unique_together = ('event',
  'recipient')`). One migration (`0002_dinnerevent_eventdish_eventinvite_delete_invite.py`)
  creates the three new models and drops `Invite` in the same step.
- ~~Location field~~ — added on `DinnerEvent`.
- ~~"Who else is coming" visibility~~ — `event_detail` shows all `EventInvite`s with
  `status='accepted'` to the host or any invited guest (`_is_host_or_guest` gate; a
  stranger who isn't host/guest gets a 404, mirroring the existing recipe-ownership
  permission pattern).
- ~~`.ics` calendar export~~ — added `event_ics` view, hand-rolled `VCALENDAR`/`VEVENT`
  text (floating local time, no `VTIMEZONE` block — acceptable per RFC5545 and far
  simpler than pulling in `icalendar`/`ics.py`), 2-hour assumed duration (no explicit
  end-time field on `DinnerEvent`).
- New views: `event_create` (replaces `invite_create` — same friend-flagging/"select all
  friends" logic reused verbatim, generalized from "one recipe" to "one or more dishes"
  picked from the host's own + liked recipes), `event_list` (hosting vs. invited, replaces
  `invite_list`), `event_detail`, `event_respond` (replaces `invite_respond`, now
  POST-only via `@require_http_methods` for consistency with the rest of the codebase —
  previously GET was silently a no-op), `event_dish_claim` (claim/unclaim; claiming an
  already-claimed dish is a no-op, not an error).
- Nav updated: "Invites" link → "Dinners" (`event_list`); recipe detail's "Invite Friend"
  link → "Host a Dinner" (`event_create` — doesn't preselect the recipe as a dish yet,
  since that would need a query-param prefill; noted as a follow-up, not built now since
  it's UI/UX polish).
- `apps/social/admin.py` updated (`DinnerEventAdmin`/`EventDishAdmin`/`EventInviteAdmin`
  replacing `InviteAdmin`); `apps/social/tests/test_views.py` fully rewritten (old
  `Invite`-based tests replaced with `TestEventCreate`/`TestEventList`/`TestEventDetail`/
  `TestEventDishClaim`/`TestEventRespond`/`TestEventIcs`).
- Explicitly deferred within this plan (unchanged from the original proposal): reminder
  emails (needs a scheduler/cron — bigger infra lift than the rest) and in-app
  notifications (already a separate tracked gap above) — not being built as part of
  this pass.

## Suggested near-term order of work

1. ~~Fix the bugs above~~ — done.
2. ~~Add `admin.py` registrations~~ — done.
3. ~~Add recipe edit/delete views~~ — done.
4. ~~Build the Friends feature~~ — done.
5. ~~Settle on a real ingredient vocabulary/encoding~~ — done (fixed 20-item vocabulary, see above).
6. ~~Add basic tests for auth, recipe CRUD, the invite flow, and the friends flow~~ — done, see "Testing" below.
7. Revisit deferred recommendation work once there are enough users/likes — see "Recommendations" below.
8. Consider a friends-list empty state nudge / registration of `Friendship` reverse-lookup UI (e.g. "who has added me as a friend") if that becomes useful later — currently only forward direction (`user1`) is surfaced.

## Recommendations

Both chosen specifically to avoid the cold-start problem: they work from day one with zero users
and don't need enough interaction data for similarity scores to be meaningful.

**1. Content-based "Similar recipes" panel — implemented 2026-07-04.** `recipe_detail` now calls
`RecipeEmbeddingService.find_similar_recipes(recipe, limit=5)` and renders a "Similar recipes" list.
Ties in cosine similarity (common with a 24-dim mostly-binary vector over a 20-word vocabulary — e.g.
any two recipes with the identical ingredient subset and tech will score 1.0 regardless of order) are
now broken by `like_count` then `created_at`, so ordering is deterministic instead of arbitrary DB
row order. Also hardened: recipes created outside the normal form flow (e.g. via `/admin/`) default
to an empty `embedding`, which previously would have crashed `cosine_similarity` on a shape mismatch —
`find_similar_recipes` now skips any recipe whose embedding length doesn't match the target's.

**3. Friends' likes aggregate — implemented 2026-07-04** (numbering kept from the original proposal
so old discussion still lines up). `FriendRecommendationService.recommend_for_user(user)` in
`apps/recommendations/services.py` aggregates `RecipeLike` rows from the user's `Friendship` list —
"recipes your friends liked, ranked by number of friends who liked it" — excluding the user's own
recipes and recipes they've already liked. Wired into `recipe_list` as a "Recommended by your
friends" section above the search form. Deliberately **not** general user-user/item-item
collaborative filtering: this is a direct aggregate query, no `numpy`/`scipy` needed, and it sidesteps
CF's usual cold-start/sparsity problem (CF needs a lot of users and interactions before similarity
scores mean anything; with a small friend graph, "what my friends liked" is a more honest use of the
actual signal available). Returns `Recipe.objects.none()` for a user with no friends yet.

**Deferred — revisit later, noted so they aren't lost:**

- **Move to real collaborative filtering once there's a good number of users/likes.** Build a sparse
  user×recipe interaction matrix from `RecipeLike` (`scipy.sparse` + `sklearn`, already a dependency)
  and do item-item CF (cosine similarity between recipe columns — "people who liked this also
  liked...") and/or user-user CF (cosine similarity between user rows). This captures taste
  correlations the content embedding can't see (e.g. two recipes that don't share any of the 20
  tagged ingredients but are liked by the same people). Revisit once there's enough like volume for
  CF similarity scores to actually outperform the current friends-aggregate baseline — with today's
  tiny data volume CF would just be noise.
- **"Recommended for you" via a user profile vector (content-based, personalized)** — proposed as
  option #2 originally, still worth doing later. Build a user's implicit taste vector as the mean (or
  recency-weighted mean) of the embeddings of recipes they've liked, then cosine-rank all recipes
  against that vector. Standard content-based user profiling — cheap, interpretable, no matrix
  factorization needed. Cold start for a user with zero likes: fall back to `popular_recipes` (already
  built) or a random sample.
- **Exploration/discovery slot.** `notes.md` calls out "occasional entirely new recipe (discovery)"
  as a stretch goal. Cheap version: replace one slot in whatever ranked list is showing (epsilon-greedy,
  ~10-20% chance) with a uniformly random recipe the user hasn't liked yet, so recommendations don't
  calcify into only ever showing near-duplicates of what's already been liked.
- **Move off brute-force cosine similarity once it's actually a bottleneck.** `find_similar_recipes`
  loops over every `Recipe` in Python per request — fine at current/expected data volume, but doesn't
  scale indefinitely. When (if) that loop shows up as a measured bottleneck (recipe count in the
  thousands+), look at precomputed/indexed vector search (pgvector, FAISS) rather than optimizing the
  Python loop itself. Don't do this preemptively — no evidence it's needed yet.
- **TF-IDF-style ingredient weighting.** The current one-hot ingredient encoding treats all 20
  ingredients as equally distinctive. Down-weighting ubiquitous ingredients (egg, onion) and
  up-weighting rare/distinctive ones would make content-based similarity sharper. Worth doing if/when
  the "Similar recipes" panel feels like it's not surfacing meaningfully different recipes — not
  needed to ship the current version.

## Testing — added 2026-07-04, collection bug fixed 2026-07-05

Runner: **pytest + pytest-django** (not Django's built-in `manage.py test`). Config in `pytest.ini`
at repo root (`DJANGO_SETTINGS_MODULE = recipe.settings`). Shared fixtures (`user`, `user_factory`,
`recipe_factory` — the latter computes a real embedding via `RecipeEmbeddingService` so
recommendation tests get realistic data) live in a root `conftest.py`. Tests live alongside each
app in `apps/<app>/tests/`.

**Correction (2026-07-05): the suite was silently under-running tests since it was first added.**
`apps/<app>/` had no `__init__.py` (intentional namespace packages) while `apps/<app>/tests/` did.
`--import-mode=importlib` was added to fix a same-basename collision (`apps/recipes/tests/test_views.py`
vs. `apps/social/tests/test_views.py`), but that flag did not actually disambiguate them: in the full
run, `apps/recipes/tests/test_views.py` and `apps/social/tests/test_views.py` were silently collected
as duplicates of `apps/accounts/tests/test_views.py`'s classes, so the real recipe/social view tests
were never executed even though the run reported "51 passed" with no errors — a false green. Caught
by running `pytest -k TestRecipeCreate` directly and getting genuine failures that the full run
didn't show at all. **Fix:** added `apps/__init__.py` and `apps/<app>/__init__.py` for every app,
making them regular (not namespace) packages so each test module gets a fully-qualified, collision-free
dotted path (`apps.recipes.tests.test_views`, not just `tests.test_views`). `--import-mode=importlib`
was left in `pytest.ini` as well (harmless, no longer load-bearing). **Lesson: a green full-suite run
is not proof the tests you think are running actually are — spot check with a targeted `-k`/file-path
run when in doubt, especially after touching pytest config.**

**One-time local setup requirement:** the app's Postgres role (`edwin`, created by `startup.sh`) had
no `CREATEDB` attribute, so pytest-django couldn't create `test_recipe_db`. Fixed by running
`ALTER USER edwin CREATEDB;` and updating `startup.sh`'s `CREATE USER` statement so fresh
installs get this automatically.

**Run it:**
- `pytest` — full suite (80 tests as of 2026-07-05, all passing).
- `pytest apps/recipes` — just one app.
- `pytest -k SomeClassName` — keyword filter (matches against test IDs, which include the
  `TestSomething` class name — e.g. `-k FriendAdd`, not `-k friend_add`, since class names are
  CamelCase).

**Coverage:** models (`RecipeLike` unique-together), forms (`CustomUserCreationForm` targets the
custom `accounts.User` — a regression test for the register-view bug fixed earlier;
`RecipeForm`/ingredient- and dietary-tag-vocabulary validation, required `title`/`instructions`),
views across all four apps (auth, recipe CRUD, comments/"made this"/collections, search filters
incl. `match_mode`/fuzzy title/dietary tags/sort, likes, dinner events incl. multi-dish/
multi-recipient creation, dish claiming, RSVP, `.ics` export, friends incl. all the edge cases from
the username-based `friend_add` work, permission checks like "only the creator can edit/delete" and
"only the host or an invited guest can view an event"), `RecipeSearchService`/
`rank_by_missing_ingredients`, and the two `apps/recommendations` services (embedding correctness,
cosine tie-breaking, the admin-created-empty-embedding guard, and
`FriendRecommendationService`'s exclusions/ranking). Deliberately **not** covered: browser-side JS
(e.g. the like button's client-side label swap) and CI wiring — noted as out of scope, not
forgotten.
