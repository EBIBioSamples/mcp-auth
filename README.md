# Python Login Portal

A lightweight **FastAPI authentication portal** for obtaining an ENA Webin authentication token and caching it temporarily in Redis.

This application is designed to support services that require Webin authentication, such as BioSamples submission workflows. A user signs in through the browser, the portal authenticates the credentials against the configured Webin token endpoint, and the returned token is stored in Redis for later use by the calling application.

## Features

- FastAPI-based web application
- Webin username/password authentication
- Jinja2 login interface
- Redis-backed token caching
- SHA-256-based cache keys
- 5-minute token cache lifetime
- Session-based success messages
- Friendly handling of invalid credentials
- Webin connection and upstream-service error handling
- Redis availability error handling
- Static CSS assets
- Unit and integration-style pytest test suite
- GitHub Actions CI support

## Authentication Flow

```text
User opens login page
        |
        v
GET /login
        |
        v
User enters Webin credentials
        |
        v
POST /login
        |
        v
FastAPI AuthService
        |
        +----> Webin authentication endpoint
        |             |
        |        Invalid credentials
        |             |
        |             v
        |      Show login error
        |
        v
Authentication successful
        |
        v
Receive authentication token
        |
        v
Store token in Redis
TTL: 300 seconds
        |
        v
Redirect to /login
        |
        v
Display success message
```

## Project Structure

```text
python_login_portal/
├── app/
│   ├── controller/
│   │   └── web_in_controller.py
│   ├── core/
│   │   ├── config.py
│   │   ├── redis.py
│   │   └── template.py
│   ├── service/
│   │   └── auth_service.py
│   ├── static/
│   │   └── style.css
│   ├── templates/
│   │   ├── base.html
│   │   └── login.html
│   └── main.py
├── tests/
├── .github/
│   └── workflows/
│       └── test.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11 or newer recommended
- Redis
- Access to the configured Webin authentication endpoint

## Installation

Clone the repository and move into the project directory:

```bash
git clone <your-repository-url>
cd python_login_portal
```

Create and activate a virtual environment:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

The application reads the following environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `WEBIN_TOKEN_URL` | Webin authentication endpoint | `https://wwwdev.ebi.ac.uk/ena/submit/webin/auth/token` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `SESSION_SECRET` | Secret used by the session middleware | `change-this-development-secret` |

For local development, you can export custom values before starting the application:

```bash
export WEBIN_TOKEN_URL="https://wwwdev.ebi.ac.uk/ena/submit/webin/auth/token"
export REDIS_URL="redis://localhost:6379/0"
export SESSION_SECRET="replace-with-a-secure-secret"
```

> Do not use the default `SESSION_SECRET` in production.

## Start Redis

If Redis is installed locally:

```bash
redis-server
```

You can verify it is available with:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

## Run the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/login
```

The root endpoint `/` automatically redirects to `/login`.

## Token Caching

After successful authentication, the returned Webin token is stored in Redis.

The cache key is created from the normalized username and a SHA-256 digest:

```text
tool-cache:<username>:<sha256-digest>
```

The token is cached for:

```text
300 seconds
```

This keeps the authentication token temporary while allowing another application or service to retrieve it during the submission workflow.

## Error Handling

The portal handles the main authentication failure scenarios:

| Scenario | HTTP Status | Behaviour |
|---|---:|---|
| Invalid Webin credentials | `401` | Displays a credentials error |
| Empty authentication token | `401` | Displays a credentials error |
| Cannot connect to Webin | `502` | Displays a Webin connectivity error |
| Unexpected Webin response | `502` | Displays an authentication-service error |
| Redis unavailable | `503` | Tells the user to contact the administrator |

## Running Tests

Run the complete test suite with:

```bash
pytest -q
```

The current project test suite contains tests for:

- FastAPI application setup
- Routes and redirects
- Login controller behaviour
- Webin authentication handling
- Successful token caching
- Invalid credentials
- Webin network failures
- Redis failures
- Redis cache key generation
- Configuration values
- Templates and static assets

At the time this README was prepared, the suite passes:

```text
28 passed
```

## GitHub Actions

The repository includes a workflow at:

```text
.github/workflows/test.yml
```

The workflow runs automatically for pushes and pull requests. It:

1. Checks out the repository.
2. Sets up Python 3.11.
3. Caches pip dependencies.
4. Installs `requirements.txt`.
5. Runs the complete pytest suite.

This helps prevent changes with failing tests from being merged unnoticed.

## Security Notes

- Never commit real Webin usernames, passwords, authentication tokens, or production secrets.
- Configure `SESSION_SECRET` securely in deployed environments.
- Use HTTPS in production and update the session middleware configuration appropriately.
- Keep the Redis instance private and protected from public access.
- Authentication tokens should remain short-lived and should not be written to application logs.

## Main Technologies

- Python
- FastAPI
- Uvicorn
- HTTPX
- Redis
- Jinja2
- Pytest
- Pytest AsyncIO
- GitHub Actions

## Development Status

The portal currently supports the core Webin authentication flow required to obtain and temporarily cache an authentication token for use by another application or service.
