# Cookie Handling Configuration

## ✅ Current Implementation

Your backend uses **HTTP-only cookies** for storing refresh tokens securely. The implementation is now **production-ready** with environment-aware settings.

---

## 🔐 Security Features

### Cookie Attributes:

1. **`httponly=true`** ✅
   - Prevents JavaScript access to cookies
   - Protects against XSS (Cross-Site Scripting) attacks
   - Always enabled

2. **`secure`** (Environment-dependent)
   - **Development**: `false` (works with HTTP localhost)
   - **Production**: `true` (requires HTTPS)
   - Only sends cookies over HTTPS when enabled

3. **`samesite`** (Environment-dependent)
   - **Development**: `lax` (works with same-site requests)
   - **Production**: `none` or `lax` depending on your frontend setup
   - Controls cross-site cookie behavior

4. **`domain`** (Optional)
   - **Development**: Not set (defaults to current domain)
   - **Production**: Set to your domain (e.g., `.yourdomain.com`)
   - Allows cookies to work across subdomains

---

## 🔧 Configuration

### Development (.env):
```env
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_HTTPONLY=true
# COOKIE_DOMAIN=  # Not set for localhost
```

### Production (Render):
**Option 1: Same Domain (Frontend and Backend on same domain)**
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_HTTPONLY=true
COOKIE_DOMAIN=.yourdomain.com
```

**Option 2: Cross-Origin (Frontend on different domain)**
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_HTTPONLY=true
# COOKIE_DOMAIN not needed for cross-origin
```

---

## 🌐 Deployment Scenarios

### Scenario 1: Backend and Frontend on Same Domain
**Example:**
- Backend: `api.myapp.com`
- Frontend: `www.myapp.com` or `myapp.com`

**Configuration:**
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.myapp.com
CORS_ORIGINS=["https://www.myapp.com","https://myapp.com"]
```

**CORS Settings:**
- `allow_credentials=true` ✅ (already set in main.py)
- Add your frontend URLs to `CORS_ORIGINS`

---

### Scenario 2: Backend and Frontend on Different Domains
**Example:**
- Backend: `myapp-backend.onrender.com`
- Frontend: `myapp.vercel.app`

**Configuration:**
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=none  # Required for cross-origin
COOKIE_HTTPONLY=true
# COOKIE_DOMAIN not set
CORS_ORIGINS=["https://myapp.vercel.app"]
```

**Important:**
- `samesite=none` **requires** `secure=true` (HTTPS)
- Frontend must send requests with `credentials: 'include'`

**Frontend Setup (JavaScript/TypeScript):**
```typescript
// Using fetch
fetch('https://myapp-backend.onrender.com/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include',  // Important!
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ email, password }),
});

// Using axios
axios.post('https://myapp-backend.onrender.com/api/v1/auth/login', 
  { email, password },
  { withCredentials: true }  // Important!
);
```

---

## 🔄 Cookie Flow

### 1. **Login/Signup** (`POST /api/v1/auth/login` or `/signup`)
- ✅ User sends credentials
- ✅ Backend validates and creates tokens
- ✅ **Access token** returned in response body (short-lived)
- ✅ **Refresh token** set in HTTP-only cookie (long-lived)

### 2. **Authenticated Requests**
- ✅ Frontend sends access token in `Authorization` header
- ✅ Cookie automatically sent by browser (no JS access)

### 3. **Token Refresh** (`POST /api/v1/auth/refresh`)
- ✅ Cookie automatically sent by browser
- ✅ Backend validates refresh token
- ✅ New access token returned
- ✅ New refresh token set in cookie (rotation)

### 4. **Logout** (`POST /api/v1/auth/logout`)
- ✅ Backend revokes refresh token in database
- ✅ Cookie deleted from browser

---

## 🐛 Troubleshooting

### Cookies Not Being Set:

#### Problem: Cookies not visible in browser
**Possible Causes:**
1. ❌ `secure=true` but using HTTP (not HTTPS)
2. ❌ `samesite=none` without `secure=true`
3. ❌ CORS not configured with `credentials: include`

**Solutions:**
- ✅ Use HTTPS in production
- ✅ Set `secure=false` for local development
- ✅ Use `samesite=lax` for local development

---

### Cookies Not Being Sent:

#### Problem: Cookies set but not sent on subsequent requests
**Possible Causes:**
1. ❌ Frontend not using `credentials: 'include'` or `withCredentials: true`
2. ❌ Domain mismatch
3. ❌ `samesite=lax` with cross-origin requests

**Solutions:**
- ✅ Add `credentials: 'include'` to all fetch requests
- ✅ Use `samesite=none` for cross-origin
- ✅ Verify CORS origins match exactly

---

### CORS Issues:

#### Problem: CORS errors in browser console
```
Access to fetch at 'https://backend.com' from origin 'https://frontend.com' 
has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' 
header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
```

**Solutions:**
- ✅ Set `CORS_ORIGINS` to your frontend URL (not `["*"]`)
- ✅ `allow_credentials=true` in CORS middleware (already set)
- ✅ Frontend uses `credentials: 'include'`

---

## 📝 Environment Variables

### Local Development (.env):
```env
# Already configured correctly for local development
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_HTTPONLY=true
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### Render Production:
```env
# Set these in Render Dashboard
COOKIE_SECURE=true
COOKIE_SAMESITE=none  # or lax if same domain
COOKIE_HTTPONLY=true
COOKIE_DOMAIN=  # Optional: .yourdomain.com for same domain
CORS_ORIGINS=["https://your-frontend-url.com"]
```

---

## ✅ Testing Cookies

### 1. **Local Testing:**
```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Use cookie
curl -b cookies.txt http://localhost:8000/api/v1/auth/refresh
```

### 2. **Browser DevTools:**
1. Open DevTools → Application → Cookies
2. Check for `refresh_token` cookie
3. Verify attributes:
   - ✅ HttpOnly: ✓
   - ✅ Secure: ✓ (in production)
   - ✅ SameSite: none/lax

### 3. **Production Testing:**
```bash
# Login (will set cookie)
curl -c cookies.txt -X POST https://your-app.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Refresh token
curl -b cookies.txt https://your-app.onrender.com/api/v1/auth/refresh
```

---

## 🔒 Security Best Practices

### ✅ Already Implemented:
1. **HTTP-only cookies** - JavaScript cannot access refresh tokens
2. **Short-lived access tokens** - 1440 minutes (24 hours)
3. **Long-lived refresh tokens** - 7 days
4. **Token rotation** - New refresh token on each refresh
5. **Token revocation** - Tokens stored in database, can be revoked
6. **Secure flag in production** - Only sent over HTTPS

### 🎯 Recommendations:
1. **Use HTTPS everywhere** - Required for secure cookies
2. **Rotate JWT secret** - Change `JWT_SECRET_KEY` periodically
3. **Monitor failed login attempts** - Add rate limiting
4. **Log security events** - Track cookie changes
5. **Set short access token lifetimes** - Currently 24 hours (good)

---

## 📚 Related Files

- **Configuration**: [config/settings.py](config/settings.py) - CookieSettings class
- **Implementation**: [utils/refresh_token_cookie.py](utils/refresh_token_cookie.py)
- **Usage**: [router/auth.py](router/auth.py) - Login, logout, refresh endpoints
- **Environment**: [.env](.env) - Local settings
- **Example**: [.env.example](.env.example) - Template
- **Deployment**: [render.yaml](render.yaml) - Production settings

---

## 🚀 Quick Start

### For Same-Domain Setup:
1. Deploy backend to Render
2. Set environment variables:
   ```env
   COOKIE_SECURE=true
   COOKIE_SAMESITE=lax
   COOKIE_DOMAIN=.yourdomain.com
   CORS_ORIGINS=["https://www.yourdomain.com"]
   ```

### For Cross-Origin Setup:
1. Deploy backend to Render
2. Set environment variables:
   ```env
   COOKIE_SECURE=true
   COOKIE_SAMESITE=none
   CORS_ORIGINS=["https://your-frontend.vercel.app"]
   ```
3. Update frontend to use `credentials: 'include'`

---

## ✨ Summary

Your cookie implementation is **production-ready** with:
- ✅ Environment-aware security settings
- ✅ HTTP-only cookies for refresh tokens
- ✅ Configurable for same-domain or cross-origin
- ✅ Proper CORS handling
- ✅ Token rotation and revocation

**Ready to deploy securely! 🔒**
