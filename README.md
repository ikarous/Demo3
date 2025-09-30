# Demo3-JWT-AuthToken

Demo3-JWT-AuthToken is a Python FastAPI demo project that demonstrates JWT-based authentication with password hashing (bcrypt), token expiration, and role-based access control using Memcached as a user store.

## Installation

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

## Running the Project

### Using Docker Compose (Recommended)

The project includes Memcached as a dependency. Start both services with:

```bash
docker-compose up
```

### Running Standalone

If you have Memcached running locally on port 11211:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
The interactive docs page will be available at `http://127.0.0.1:8000/docs`.

## Endpoints

- `POST /token`
  Exchange username and password for a short-lived bearer token (JWT). Token expires in 2 minutes (intentionally short for demonstration).

- `GET /protected`
  Returns a personalized message. Requires an `Authorization: Bearer <token>` header.

- `GET /protected2`
  Admin-only route demonstrating role-based access control. Requires authentication AND admin privileges.

## Example Requests

### Get a Token

```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepassword"}'
```

Example Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer"
}
```

### Use the Token

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepassword"}' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl http://127.0.0.1:8000/protected -H "Authorization: Bearer $TOKEN"
```

Example Response:

```json
{
  "message": "Hello, Alice Smith! This is a protected endpoint."
}
```

### Test Token Expiration

Wait 2+ minutes after getting a token, then try to use it:

```bash
curl http://127.0.0.1:8000/protected -H "Authorization: Bearer $TOKEN"
```

Expected Response:

```json
{
  "detail": "Token expired"
}
```

### Test Admin Route

```bash
# Non-admin user (will fail with 403)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepassword"}' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl http://127.0.0.1:8000/protected2 -H "Authorization: Bearer $TOKEN"

# Admin user (will succeed)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpassword"}' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl http://127.0.0.1:8000/protected2 -H "Authorization: Bearer $TOKEN"
```

## Key Features Demonstrated

- **JWT Token Generation**: Stateless authentication using signed tokens
- **Password Hashing**: Passwords stored using bcrypt (secure, slow hashing)
- **Token Expiration**: 2-minute token lifetime to demonstrate expiration handling
- **Authentication vs Authorization**:
  - 401 Unauthorized: Invalid/expired token
  - 403 Forbidden: Valid token but insufficient permissions
- **Role-Based Access Control**: Admin-only routes with permission checks
- **Memcached Integration**: User data stored in Memcached (simulates database)

---

⚠️ **Note**: This demo uses hardcoded secrets and a 2-minute token expiration for educational purposes.
In a real application:
- Use environment variables for secrets
- Use longer token expiration times (30-60 minutes)
- Implement refresh tokens
- Use a proper database with connection pooling
- Add rate limiting on login endpoint
- Use HTTPS in production
