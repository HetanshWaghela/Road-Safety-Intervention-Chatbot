# Backend Deployment Guide 🚀

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway will auto-detect `railway.json` in `backend/` folder
5. Set environment variables:
   ```
   GEMINI_API_KEY=your_gemini_key
   API_KEYS=key1,key2,key3
   ENVIRONMENT=production
   LOG_LEVEL=info
   ```
6. Deploy! Railway will give you a URL like: `https://your-app.railway.app`

### Option 2: Render
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo
4. Settings:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend`
5. Environment Variables:
   ```
   GEMINI_API_KEY=your_gemini_key
   API_KEYS=key1,key2,key3
   PORT=8000
   ```
6. Deploy!

### Option 3: Fly.io
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. In `backend/` directory: `fly launch`
3. Set secrets:
   ```bash
   fly secrets set GEMINI_API_KEY=your_key
   fly secrets set API_KEYS=key1,key2,key3
   ```
4. Deploy: `fly deploy`

## Important Notes

### ✅ Data Files Included
- `interventions.json` (50 interventions) - ✅ Included in Docker image
- `chroma_db/` (vector store) - ✅ Included in Docker image
- Database is ready to use!

### ✅ CORS Configuration
- Backend already has CORS enabled for all origins
- Will work with Streamlit Cloud frontend

### ✅ Health Check
- Endpoint: `/health`
- Used by deployment platforms for monitoring

## After Deployment

1. **Get your backend URL**: e.g., `https://your-backend.railway.app`
2. **Update Streamlit Cloud environment variables**:
   ```
   API_URL=https://your-backend.railway.app
   API_KEY=one_of_your_api_keys
   ```
3. **Test**: Visit your Streamlit app and click "Test Connection"

## Troubleshooting

### Database not found?
- Data files are included in Docker image
- If issues, check logs: `railway logs` or Render dashboard

### CORS errors?
- Backend has CORS enabled for all origins
- Should work automatically

### API key errors?
- Make sure `API_KEYS` environment variable has comma-separated keys
- Frontend must use one of these keys

## Ready! 🎉

Your backend is ready to deploy. Choose a platform and follow the steps above!

