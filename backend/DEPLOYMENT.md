# Render Deployment Guide

## ✅ Your Backend is Ready for Render Deployment!

### Changes Made:

1. ✅ **Created `requirements.txt`** - Copied from requirements.ini for Python package management
2. ✅ **Created `render.yaml`** - Render service configuration file
3. ✅ **Created `.renderignore`** - Excludes unnecessary files from deployment
4. ✅ **Updated upload directory** - Changed default from `./app/uploads` to `/tmp/uploads` for production
5. ✅ **Already using cloud services**:
   - MongoDB Atlas (cloud database)
   - Chroma Cloud (vector storage)
   - GridFS (file storage in MongoDB)

---

## Deployment Steps:

### 1. **Push Your Code to GitHub**

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. **Create Render Account**
- Go to https://render.com
- Sign up with your GitHub account

### 3. **Deploy from Dashboard**

#### Option A: Using render.yaml (Recommended)
1. Click **"New +"** → **"Blueprint"**
2. Connect your GitHub repository
3. Render will automatically detect `render.yaml`
4. Click **"Apply"**

#### Option B: Manual Setup
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `multimodal-rag-backend`
   - **Region**: Oregon (or your preferred region)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### 4. **Set Environment Variables**

In Render Dashboard → Your Service → Environment:

```env
# Required - Add these in Render dashboard
MONGODB_URI=your_mongodb_atlas_uri
MONGODB_DATABASE=agentic_rag_db
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key
CORS_ORIGINS=["https://your-frontend-url.com"]

# Cookie Settings (Important for Authentication!)
# For same-domain setup (frontend and backend on same domain):
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.yourdomain.com

# For cross-origin setup (frontend and backend on different domains):
# COOKIE_SECURE=true
# COOKIE_SAMESITE=none
# COOKIE_DOMAIN=  # Leave empty

# Chroma Cloud
CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_chroma_tenant
CHROMA_HOST=api.trychroma.com
CHROMA_DATABASE=multimodal_rag

# Optional APIs
TAVILY_API_KEY=your_tavily_api_key
UNSTRUCTURED_API_KEY=your_unstructured_api_key
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agentic-multimodal-rag

# Upload settings (already configured correctly)
UPLOAD_DIRECTORY=/tmp/uploads
```

### 5. **Deploy!**
- Click **"Create Web Service"** or **"Apply Blueprint"**
- Render will build and deploy your app
- Check the logs for any errors

---

## Health Checks

After deployment, verify these endpoints:

1. **Health Check**: `https://your-app.onrender.com/health`
2. **Readiness Check**: `https://your-app.onrender.com/health/ready`
3. **API Docs**: `https://your-app.onrender.com/docs`

---

## Important Notes:

### ✅ **What Works Well:**
- **GridFS**: Files stored in MongoDB Atlas (persistent)
- **Chroma Cloud**: Vectors stored in cloud (persistent)
- **MongoDB Atlas**: Database in cloud (persistent)
- **Temp Files**: Automatically cleaned up after processing

### ⚠️ **Render Free Tier Limitations:**
- **Cold starts**: App sleeps after 15 minutes of inactivity
- **Build time**: 15 minutes max
- **Memory**: 512MB RAM
- **Disk**: Ephemeral (resets on restart - but we're not storing files locally!)

### 🚀 **Production Recommendations:**
1. **Upgrade to Render Starter plan** ($7/mo) for:
   - No cold starts
   - More resources
   - Better performance

2. **Environment Variables**:
   - Never commit `.env` to git
   - Set all secrets in Render dashboard
   - Use `.env.example` as reference

3. **CORS Configuration**:
   - Update `CORS_ORIGINS` with your frontend URL
   - Format: `["https://frontend.com","https://www.frontend.com"]`

4. **MongoDB Atlas**:
   - Whitelist Render's IP: `0.0.0.0/0` (for dynamic IPs)
   - Or use Render's static IPs (paid feature)

---

## Troubleshooting:

### Build Fails:
```bash
# Check Python version compatibility
# Render uses Python 3.12 by default (matches your setup)
```

### Deploy Fails:
- Check environment variables are set correctly
- Verify MongoDB connection string
- Check logs in Render dashboard

### App Crashes:
- Check memory usage (upgrade if needed)
- Verify all environment variables are set
- Check MongoDB Atlas network access

### CORS Errors:
- Update `CORS_ORIGINS` with your frontend URL
- Ensure format is correct JSON array

---

## Local vs Production:

### Local Development (Current):
```env
UPLOAD_DIRECTORY=./data/uploads
```

### Production (Render):
```env
UPLOAD_DIRECTORY=/tmp/uploads
```

The app automatically handles both! Files in `/tmp` are temporary and get cleaned after processing.

---

## Post-Deployment Checklist:

- [ ] All environment variables set in Render
- [ ] Cookie settings configured for your deployment type
- [ ] MongoDB Atlas accepts connections from `0.0.0.0/0`
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/health/ready` shows MongoDB connected
- [ ] `/docs` accessible for API documentation
- [ ] Frontend CORS configured correctly
- [ ] Frontend sends `credentials: 'include'` with requests
- [ ] Test login and verify cookies are set
- [ ] Test document upload functionality
- [ ] Test query functionality

---

## 🍪 Cookie Configuration

**Important**: Your backend uses HTTP-only cookies for refresh tokens. This requires specific configuration based on your deployment setup.

### Same-Domain Setup:
If your frontend and backend are on the same domain (e.g., `app.yourdomain.com` and `api.yourdomain.com`):

```env
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.yourdomain.com
CORS_ORIGINS=["https://app.yourdomain.com"]
```

### Cross-Origin Setup:
If your frontend and backend are on different domains (e.g., `myapp.vercel.app` and `myapp-backend.onrender.com`):

```env
COOKIE_SECURE=true
COOKIE_SAMESITE=none  # Required for cross-origin!
CORS_ORIGINS=["https://myapp.vercel.app"]
```

**Frontend Requirement**: Your frontend **must** send `credentials: 'include'` with all API requests:

```typescript
// Fetch API
fetch('https://api-url.com/api/v1/auth/login', {
  credentials: 'include',  // Important!
  // ... other options
});

// Axios
axios.post('url', data, { 
  withCredentials: true  // Important!
});
```

📖 **See [COOKIE_HANDLING.md](COOKIE_HANDLING.md) for complete cookie documentation**

---

## Your Current Status:

✅ **Backend Code**: Ready for deployment
✅ **Dependencies**: All cloud-based (MongoDB Atlas, Chroma Cloud)
✅ **File Storage**: GridFS (persistent)
✅ **Configuration**: Optimized for cloud deployment
✅ **Health Checks**: Implemented
✅ **Error Handling**: Implemented

**You're ready to deploy! 🚀**
