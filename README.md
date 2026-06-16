# FastAPI Notes

---

## HTTP Methods

* **PUT** – Replaces the entire resource. If some fields are missing, they will be replaced with default values or `null`.
* **PATCH** – Updates specific fields of a resource. Only the fields provided in the request will be updated.
* **DELETE** – Ideally returns **HTTP 204 No Content**. There is no response model, only a status code.

---

## HTTP Status Codes

* **200 OK** – Successful `GET`, `PUT`, `PATCH`
* **201 CREATED** – Successful `POST`
* **204 NO CONTENT** – Successful `DELETE`
* **400 BAD REQUEST** – Duplicate username/email
* **401 UNAUTHORIZED** – User is not authenticated (not logged in)
* **403 FORBIDDEN** – User is not allowed to edit/delete another user's resource
* **404 NOT FOUND** – Resource doesn't exist
* **422 UNPROCESSABLE ENTITY** – Validation error (automatic from Pydantic)

---

## Async

* Allows a program to handle multiple tasks concurrently.
* Used to avoid waiting for external operations (I/O-bound tasks):

  1. Database requests
  2. Network responses (external API calls)
  3. File reads
* Async lets us do other work while waiting for these operations.
* Does **not** help with CPU-bound tasks like image processing or heavy calculations.
* Async isn't always faster; its benefits appear under concurrent load.
* Don't use synchronous database sessions in async routes.
* Don't use synchronous libraries like `requests` in async routes.

### FastAPI Async

* FastAPI runs normal `def` functions in a separate thread pool, preventing them from blocking the main event loop.
* FastAPI runs `async def` functions directly in the main event loop, which is more efficient.
* You must `await` I/O operations (e.g., database operations).
* Blocking the main event loop is much worse than using a regular `def`.
* `aiosqlite` provides an async driver for SQLAlchemy.

### Lazy Loading

* Probably the biggest difference between sync and async SQLAlchemy.
* Lazy loading allows access to relationships (e.g., `post.author`) by automatically running another query.
* In Async SQLAlchemy, accessing `post.author` without loading it first raises an error because it would require a synchronous query in an async context.
* **Solution:** Use eager loading with `selectinload()`. Any query that accesses relationships should use eager loading.

---

## Pydantic

* A data validation library that uses Python type hints.
* Used for validation, serialization, and documentation.
* Enforces type hints at runtime and provides detailed errors.
* Determines what we accept and return from API endpoints.
* Frontend template routes still use dictionaries and don't know about Pydantic.
* Schemas only apply to API endpoints where a `response_model` is defined.

---

## SQLite & SQLAlchemy

* **SQLite** – Built into Python and requires no separate server installation.
* **SQLAlchemy** – The most popular ORM for Python.
* **Benefit of an ORM** – We can switch databases with mostly configuration changes.
* Pydantic schemas and database models are created separately.
* `sqlmodel` can combine them, but we're keeping them separate to understand both concepts better, and most industry-standard apps don't use `sqlmodel`.

---

## Authentication & Authorization

* **Authentication** – Who are you?
* **Authorization** – What are you allowed to do?

---

## Security & Configuration

* **`pwdlib[argon2]`** – Used for password hashing. Argon2 is considered the most secure hashing algorithm.
* **`pyjwt` (JSON Web Tokens)** – Used for authentication and authorization. JWTs are like encrypted cookies that store user information and permissions. They are stateless, work across different servers without a shared session store, and are more secure than traditional cookies because they are signed and can expire.
* **`pydantic-settings` (over `python-dotenv`)** – Centralizes configuration in one settings module, provides clear errors, automatically validates settings with Pydantic, and uses secret strings to reduce the risk of data leaks.
