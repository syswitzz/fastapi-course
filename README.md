# FastAPI Notes

## Why FastAPI?

* Easy to use.
* Async by default.

---

## Request Flow

```text
Client
  ↓
FastAPI
  ↓
Pydantic (validates data)
  ↓
SQLAlchemy (talks to DB)
  ↓
SQLite (stores data)
```

---

## Pydantic

* Pydantic is a data validation and parsing library for Python.
* While Python is dynamically typed, Pydantic uses type hints to enforce data structures at runtime, ensuring the data your application processes is exactly what you expect.
* Used for validation, serialization, and documentation.
* Enforces type hints at runtime and provides detailed errors.
* Determines what we accept and return from API endpoints.
* Frontend template routes still use dictionaries and don't know about Pydantic.
* Schemas only apply to API endpoints where a `response_model` is defined.

### BaseModel

The `BaseModel` is the fundamental building block of Pydantic. By creating a class that inherits from `BaseModel`, you define a schema for your data.

* Checks that incoming data matches your defined types.
* Attempts to convert data to the correct type when possible.
* Allows you to convert complex objects into:

  * Python dictionaries: `.model_dump()`
  * JSON strings: `.model_dump_json()`

### FastAPI Response Model

A FastAPI response model is a Pydantic model used to define, validate, serialize, and filter the structure and data types of responses sent back to a client from an API endpoint.

* Only fields defined in the response model are included in the final JSON response. Extra data in internal Python objects (e.g., database objects) is automatically filtered out.
* Converts complex Python data types (e.g., `datetime` objects or database models) into JSON-compatible formats automatically.
* FastAPI uses the response model to automatically generate the JSON Schema for OpenAPI documentation.

---

## SQLite & SQLAlchemy

* **SQLite** – Built into Python and requires no separate server installation.
* **SQLAlchemy** – The most popular ORM for Python.
* **Benefit of an ORM** – We can switch databases with mostly configuration changes.
* Pydantic schemas and database models are created separately.
* `sqlmodel` can combine them, but we're keeping them separate to understand both concepts better, and most industry-standard apps don't use `sqlmodel`.

---

## Async

* Allows a program to handle multiple tasks concurrently.
* Mainly useful for I/O-bound tasks:

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

## HTTP Methods

* **PUT** – Replaces the entire resource. Missing fields are replaced with default values or `null`.
* **PATCH** – Updates specific fields of a resource. Only provided fields are updated.
* **DELETE** – Ideally returns **HTTP 204 No Content** with no response body.

---

## HTTP Status Codes

* **100-199** – Informational responses
* **200-299** – Successful responses
* **300-399** – Redirection messages
* **400-499** – Client-side errors
* **500-599** – Server-side errors

### Common Status Codes

* **200 OK** – Successful `GET`, `PUT`, `PATCH`
* **201 CREATED** – Successful `POST`
* **204 NO CONTENT** – Successful `DELETE`
* **400 BAD REQUEST** – Duplicate username/email
* **401 UNAUTHORIZED** – User is not authenticated (not logged in)
* **403 FORBIDDEN** – User is not allowed to edit/delete another user's resource
* **404 NOT FOUND** – Resource doesn't exist
* **422 UNPROCESSABLE ENTITY** – Validation error (automatic from Pydantic)

---

## Authentication & Authorization

* **Authentication** – Who are you?
* **Authorization** – What are you allowed to do?

---

## Security & Configuration

* **`pwdlib[argon2]`** – Used for password hashing. Argon2 is considered the most secure hashing algorithm.

* **`pyjwt` (JSON Web Tokens)** – Used for authentication and authorization. JWTs are like encrypted cookies that store user information and permissions. They are stateless, work across different servers without a shared session store, and are more secure than traditional cookies because they are signed and can expire.

* **`pydantic-settings` (over `python-dotenv`)** – Centralizes configuration in one settings module, provides clear errors, automatically validates settings with Pydantic, and uses secret strings to reduce the risk of data leaks.

---

## Running FastAPI

**Run the server**

```bash
uv run uvicorn main:app --reload
```

**POST request (query parameter)**

```bash
curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:8000/items?item=apple'
```

**POST request (JSON body)**

```bash
curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:8000/items' -d '{"task": "apple"}'
```

**GET request**

```bash
curl -X GET 'http://127.0.0.1:8000/items'
```

**Swagger UI**

```text
http://127.0.0.1:8000/docs#/
```
