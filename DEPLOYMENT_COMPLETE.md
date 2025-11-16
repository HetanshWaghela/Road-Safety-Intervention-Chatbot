# Complete Deployment Guide - Scenario 2 🚀

## Overview
Deploy both **Backend** and **Frontend** so everything works 24/7, even when you close Cursor.

---

## Step 1: Deploy Backend ⚙️

### Option A: Railway (Easiest - Recommended)

1. **Go to [railway.app](https://railway.app)** and sign up/login
2. **New Project** → **Deploy from GitHub repo**
3. **Select your repository**
4. **Railway will auto-detect** `backend/railway.json`
5. **Set Environment Variables** in Railway dashboard:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   API_KEYS=key1,key2,key3
   ENVIRONMENT=production
   LOG_LEVEL=info
   PORT=8000
   ```
6. **Deploy!** Railway will build and deploy automatically
7. **Get your backend URL**: e.g., `https://your-app.railway.app`
8. **Test**: Visit `https://your-app.railway.app/health`

### Option B: Render

1. Go to [render.com](https://render.com)
2. **New** → **Web Service**
3. Connect your GitHub repo
4. **Settings**:
   - **Name**: `road-safety-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   API_KEYS=key1,key2,key3
   ```
6. **Deploy!**

---

## Step 2: Deploy Frontend 🎨

### Streamlit Cloud

1. **Go to [streamlit.io/cloud](https://streamlit.io/cloud)**
2. **Sign up/Login** with GitHub
3. **New app** → **From existing repo**
4. **Select your repository**
5. **Configuration**:
   - **Main file path**: `frontend/app.py`
   - **Python version**: 3.8+ (auto-detected)
6. **Advanced settings** → **Secrets**:
   ```
   API_URL=https://your-backend.railway.app
   API_KEY=one_of_your_api_keys_from_backend
   ```
7. **Deploy!**

---

## Step 3: Test Everything ✅

1. **Backend Health Check**: Visit `https://your-backend.railway.app/health`
   - Should return: `{"status": "healthy", ...}`

2. **Frontend Test**: Visit your Streamlit app
   - Click **"Test Connection"** in sidebar
   - Should show: ✅ Connection successful!

3. **Full Test**: Try a search query
   - Should return results with IRC references

---

## What's Included in Deployment ✅

### Backend
- ✅ 50 interventions database (`interventions.json`)
- ✅ Vector store (`chroma_db/`)
- ✅ All dependencies
- ✅ CORS enabled for frontend
- ✅ Health check endpoint

### Frontend
- ✅ All UI components
- ✅ Error handling
- ✅ Loading states
- ✅ IRC references prominently displayed

---

## Environment Variables Summary

### Backend (Railway/Render)
```
GEMINI_API_KEY=your_gemini_key
API_KEYS=key1,key2,key3
ENVIRONMENT=production
LOG_LEVEL=info
```

### Frontend (Streamlit Cloud)
```
API_URL=https://your-backend-url.com
API_KEY=one_of_your_backend_api_keys
```

---

## Troubleshooting

### Backend not accessible?
- Check Railway/Render logs
- Verify environment variables are set
- Check CORS settings (already enabled)

### Frontend can't connect?
- Verify `API_URL` is correct (no trailing slash)
- Verify `API_KEY` matches one from backend `API_KEYS`
- Check browser console for errors

### Database not found?
- Data files are included in Docker image
- Check deployment logs for initialization

---

## Success! 🎉

Once both are deployed:
- ✅ Backend runs 24/7 on Railway/Render
- ✅ Frontend runs 24/7 on Streamlit Cloud
- ✅ Works even when you close Cursor
- ✅ Accessible from anywhere

**You're all set!** 🚀

