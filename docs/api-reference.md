# LBAL API Reference

This document lists the HTTP endpoints currently exposed by the LBAL backend so the frontend team can integrate without digging through the codebase. All paths below are relative to the FastAPI root (e.g. `https://api.lbal.local`). Unless noted otherwise, requests and responses use JSON and timestamps are ISO8601 strings in UTC.

## Common Conventions

- **Authentication**: Bearer access tokens issued by `/auth/login`, `/auth/google`, or `/auth/verify-email` must be sent as `Authorization: Bearer <token>`. Refresh tokens are opaque strings returned alongside access tokens.
- **Rate limiting**:
  - Login attempts share a per-IP limiter.
  - Listing creation and media presign endpoints are throttled per user ID.
- **Errors**: Validation errors and domain errors respond with an `{"detail": "..."}` payload plus an optional `code` field when raised through `ApplicationError`.
- **Pagination**: Listing searches accept `page` and `page_size` query parameters (default 1 and 20, max page size 50).

---

## Auth Endpoints (`/auth`)

### `POST /auth/signup`
Create a user account and send an email verification code. No auth required.

**Request**
```json
{
  "name": "Jane Founder",
  "email": "jane@example.com",
  "password": "Sup3rSecret!"
}
```

**201 Response**
```json
{
  "message": "Verification code sent"
}
```

### `POST /auth/verify-email`
Confirm a newly created account using the emailed code. Returns an authenticated session bundle.

**Request**
```json
{
  "email": "jane@example.com",
  "code": "123456"
}
```

**200 Response**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<refresh>",
  "token_type": "bearer",
  "session_id": "fe87b4b4-2f9f-4b5c-92eb-9828d931dc91",
  "user": {
    "id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53",
    "name": "Jane Founder",
    "email": "jane@example.com",
    "role": "user",
    "avatar_url": null,
    "is_active": true
  }
}
```

### `POST /auth/resend-verification`
Trigger another verification email.

**Request**
```json
{ "email": "jane@example.com" }
```

**200 Response**
```json
{ "message": "Verification code sent" }
```

### `POST /auth/login`
Password-based sign-in. Protected by `enforce_login_rate_limit`.

**Request**
```json
{
  "email": "jane@example.com",
  "password": "Sup3rSecret!"
}
```

**200 Response**: same shape as `verify-email`.

### `POST /auth/google`
Exchange a Google ID token for LBAL credentials. Requires the frontend to retrieve a valid `id_token`.

**Request**
```json
{ "id_token": "<google-id-token>" }
```

### `POST /auth/refresh`
Issue a new access token bundle using a refresh token. The refresh token may be sent in the body or as a bearer token header.

**Request**
```json
{ "refresh_token": "<refresh>" }
```

**200 Response**: same as login, with a new `session_id`.

### `POST /auth/logout`
Invalidate the refresh token belonging to the current session. If the request body is omitted, only the current session is revoked. Requires sending the refresh token as a bearer token (no auth header = 400).

**Optional Request**
```json
{ "all": true }
```

### `POST /auth/logout-all`
Authenticated endpoint that removes every session for the current user.

**200 Response**
```json
{ "detail": "All sessions revoked" }
```

---

## User Profile (`/users`)

Authentication: all endpoints require a valid access token.

### `GET /users/me`
Return the hydrated profile for the logged-in user.

**200 Response**
```json
{
  "id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53",
  "name": "Jane Founder",
  "email": "jane@example.com",
  "phone": "+212600000000",
  "avatar_url": "https://cdn.lbal.com/u/8f20/avatar.png",
  "role": "user",
  "language": "fr",
  "is_active": true
}
```

### `PUT /users/me`
Partial update of profile attributes. Only provided fields are changed.

**Request**
```json
{
  "name": "Jane F.",
  "phone": "+212699999999",
  "avatar_url": "https://cdn.lbal.com/u/8f20/avatar.png",
  "language": "en"
}
```

**200 Response**: same shape as `GET /users/me`.

---

## Address Book (`/users/me/addresses`)

All endpoints require auth. Only the owning user may mutate an address.

### `POST /users/me/addresses`
Create a shipping address. Set `is_default=true` to promote it.

**Request**
```json
{
  "line1": "221B Baker Street",
  "line2": "Apt 4",
  "city": "Casablanca",
  "state": "Grand Casablanca",
  "postal_code": "20000",
  "country": "MA",
  "is_default": true
}
```

**201 Response**
```json
{
  "id": "c0b7536a-fa96-425f-8887-8a3c2404d0a6",
  "user_id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53",
  "line1": "221B Baker Street",
  "line2": "Apt 4",
  "city": "Casablanca",
  "state": "Grand Casablanca",
  "postal_code": "20000",
  "country": "MA",
  "is_default": true,
  "created_at": "2025-01-18T11:45:00Z"
}
```

### `GET /users/me/addresses`
List every address for the current user.

**200 Response**
```json
[
  {
    "id": "c0b7536a-fa96-425f-8887-8a3c2404d0a6",
    "user_id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53",
    "line1": "221B Baker Street",
    "line2": "Apt 4",
    "city": "Casablanca",
    "state": "Grand Casablanca",
    "postal_code": "20000",
    "country": "MA",
    "is_default": true,
    "created_at": "2025-01-18T11:45:00Z"
  }
]
```

### `PUT /users/me/addresses/{address_id}`
Update a specific address. All fields optional.

**Request**
```json
{
  "line1": "45 New Street",
  "city": "Rabat",
  "is_default": false
}
```

### `DELETE /users/me/addresses/{address_id}`
Remove an address. Returns `204 No Content`.

---

## Listings (`/listings`)

### `GET /listings`
Public search endpoint that supports filtering and pagination.

**Query params**
- `page` (default 1), `page_size` (default 20, max 50)
- `category_id`, `city`, `condition`, `min_price`, `max_price`
- `sort_by`: `price | newest | oldest` (default `newest`)

**200 Response**
```json
{
  "items": [
    {
      "id": "2cef6666-0a34-4e71-acdd-8152d39a0bd9",
      "user_id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53",
      "title": "Near-new sneakers",
      "description": "Size 42, worn once.",
      "category_id": "2174af61-e5d4-4f96-a91f-5e2af00f2fbb",
      "brand": "Nike",
      "size": "42",
      "condition": "excellent",
      "price": "650.00",
      "city": "Casablanca",
      "status": "published",
      "created_at": "2025-01-20T13:23:11Z",
      "updated_at": "2025-01-20T13:23:11Z",
      "images": []
    }
  ],
  "total": 37,
  "page": 1,
  "page_size": 20
}
```

### `POST /listings`
Create a listing. Requires auth and respects the listing creation rate limit.

**Request**
```json
{
  "title": "Vintage leather jacket",
  "description": "Size M, imported from Italy.",
  "category_id": "2174af61-e5d4-4f96-a91f-5e2af00f2fbb",
  "brand": "Gucci",
  "size": "M",
  "condition": "good",
  "price": "3200.00",
  "city": "Marrakesh"
}
```

**201 Response**: full `ListingResponse` object.

### `GET /listings/me`
Return every listing authored by the logged-in user.

### `GET /listings/{listing_id}`
Public listing detail endpoint.

### `PUT /listings/{listing_id}`
Update a listing that belongs to the current user. Accepts the same fields as the create endpoint, but all optional.

### `DELETE /listings/{listing_id}`
Delete a listing owned by the current user. Returns `204 No Content`.

#### Listing Images

- `POST /listings/{listing_id}/images`: attach an already-uploaded image URL to a listing with an optional `position`.
  ```json
  { "url": "https://cdn.lbal.com/listings/2cef/img1.jpg", "position": 0 }
  ```
  Response: `ListingImageResponse`.

- `DELETE /listings/images/{image_id}`: remove a specific image. Response `{"detail": "deleted"}`.

- `POST /listings/{listing_id}/images/presign`: generate a temporary S3 upload URL for an image. Requires auth, checks ownership, and needs a JSON body:
  ```json
  { "content_type": "image/jpeg" }
  ```
  Response:
  ```json
  {
    "upload_url": "https://s3.amazonaws.com/...signature",
    "final_url": "https://cdn.lbal.com/listings/2cef/uuid.jpg"
  }
  ```

---

## Categories (`/categories`)

`GET /categories` returns the full list to drive dropdowns. Public endpoint.

**Response**
```json
[
  { "id": "2174af61-e5d4-4f96-a91f-5e2af00f2fbb", "name": "Shoes" },
  { "id": "bb8f81e1-96a8-4c4e-8239-a2aadb5d1e25", "name": "Jackets" }
]
```

---

## Media (`/media`)

- `GET /media/ping`: simple health probe.
- `POST /media/presign`: placeholder that currently echoes the requesting user ID and enforces the media presign rate limiter. Use for early integration tests until the S3 logic in `/listings/{listing_id}/images/presign` is preferred.

**Response**
```json
{
  "message": "Presign endpoint placeholder",
  "user_id": "8f20b883-1c37-4820-a2a6-ff3fc5010a53"
}
```

---

## Health & Misc

- `GET /health`: returns `{"status": "ok"}` and is unauthenticated.
- `GET /admin/ping`, `/orders/ping`, `/wallet/ping`, `/shipments/ping`, `/disputes/ping`: lightweight router checks returning the router name and `"ok"` status. Useful for monitoring; no payloads beyond the static response.

---

## Testing Checklist for Frontend

1. Acquire tokens via signup → verify-email or login flow.
2. Call protected endpoints with `Authorization: Bearer <access_token>`.
3. Refresh tokens before expiry using `/auth/refresh`; update stored session bundle.
4. For uploads: presign (either `/media/presign` placeholder or `/listings/{id}/images/presign`), upload directly to S3, then attach final URL to listing via `POST /listings/{id}/images`.
5. Respect pagination defaults when consuming listing search responses.
