# Auth

Login/register views and token storage (e.g. Keychain). Maps to
`POST /api/v1/auth/token/` and `POST /api/v1/accounts/register/`, both of which return
`{"token": "..."}` for use as `Authorization: Token <token>` on all other requests.
