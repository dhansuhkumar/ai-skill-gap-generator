# Deployment Guide

This guide provides step-by-step instructions for deploying the AI Skill Gap Generator to production using Render (backend) and Vercel (frontend).

## Prerequisites

- GitHub repository with your code
- Render account (https://render.com)
- Vercel account (https://vercel.com)
- Supabase project with database set up (see [DATABASE_SETUP.md](DATABASE_SETUP.md))

---

## Backend Deployment (Render)

### 1. Create New Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the `ai-skill-gap-generator` repository

### 2. Configure Build Settings

Render should auto-detect the settings from `render.yaml`, but verify:

- **Name:** `ai-skill-gap-generator-backend`
- **Region:** Oregon (or closest to your users)
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements-prod.txt`
- **Start Command:** `gunicorn backend.run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3. Set Environment Variables

In the Render dashboard, add these environment variables:

| Variable Name | Value | Notes |
|--------------|-------|-------|
| `JWT_SECRET_KEY` | `your-super-secret-key-123` | Use a strong random string in production |
| `SUPABASE_URL` | `https://kquhgkomsqlbqjigxmiz.supabase.co` | Your Supabase project URL |
| `SUPABASE_KEY` | `eyJhbGci...` | Your Supabase anon key |
| `CORS_ALLOWED_ORIGINS` | `https://ai-skill-gap-generator.vercel.app` | Your Vercel frontend URL |
| `PYTHON_VERSION` | `3.11.0` | Python version |

> **⚠️ IMPORTANT:** Make sure to use `SUPABASE_URL` and `SUPABASE_KEY` (NOT `VITE_SUPABASE_URL`). The `VITE_` prefix is only for frontend environment variables.

### 4. Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, your backend will be available at: `https://ai-skill-gap-generator.onrender.com`

### 5. Verify Backend

Test the health endpoint:
```bash
curl https://ai-skill-gap-generator.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "message": "Application is running"}
```

---

## Frontend Deployment (Vercel)

### 1. Import Project

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Select the `ai-skill-gap-generator` repository

### 2. Configure Project Settings

- **Framework Preset:** Vite (auto-detected)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build` (auto-detected)
- **Output Directory:** `dist` (auto-detected)

### 3. Set Environment Variables

In the Vercel project settings → Environment Variables, add:

| Variable Name | Value | Environment |
|--------------|-------|-------------|
| `VITE_API_URL` | `https://ai-skill-gap-generator.onrender.com` | Production, Preview, Development |
| `VITE_SUPABASE_URL` | `https://kquhgkomsqlbqjigxmiz.supabase.co` | Production, Preview, Development |
| `VITE_SUPABASE_KEY` | `eyJhbGci...` | Production, Preview, Development |

> **💡 TIP:** The `VITE_` prefix is required for Vite to expose these variables to the browser.

### 4. Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (2-5 minutes)
3. Your frontend will be available at: `https://ai-skill-gap-generator.vercel.app`

### 5. Verify Frontend

1. Visit `https://ai-skill-gap-generator.vercel.app`
2. Open browser DevTools (F12) → Console
3. Check for errors:
   - ✅ No "Supabase credentials not configured" warnings
   - ✅ No CORS errors
   - ✅ API calls go to `https://ai-skill-gap-generator.onrender.com`

---

## Post-Deployment Testing

### Test Full User Flow

1. **Sign Up / Sign In**
   - Create a new account or sign in
   - Verify JWT token is stored

2. **Upload Resume**
   - Upload a PDF resume
   - Verify skills are extracted

3. **View Dashboard**
   - Check that skills are displayed
   - Verify skill match percentage

4. **Generate Learning Path**
   - Click "Generate Learning Path"
   - Verify AI-generated content appears
   - Check that YouTube links work

---

## Troubleshooting

### CORS Errors

**Symptom:** Console shows "blocked by CORS policy"

**Solution:**
1. Verify `CORS_ALLOWED_ORIGINS` in Render includes your exact Vercel URL
2. Make sure there are no trailing slashes
3. Redeploy backend after changing environment variables

### Supabase Not Configured

**Symptom:** Console shows "Supabase credentials not configured"

**Solution:**
1. Check that `VITE_SUPABASE_URL` and `VITE_SUPABASE_KEY` are set in Vercel
2. Verify the values are correct (copy from Supabase dashboard)
3. Redeploy frontend after adding environment variables

### 404 Errors on API Endpoints

**Symptom:** Console shows "Failed to load resource: 404"

**Solution:**
1. Verify `VITE_API_URL` in Vercel points to your Render backend URL
2. Check that backend is running (visit `/health` endpoint)
3. Ensure API routes are registered correctly in `backend/app/__init__.py`

### Backend Crashes on Startup

**Symptom:** Render logs show errors during startup

**Solution:**
1. Check Render logs for specific error messages
2. Verify all required environment variables are set
3. Ensure `requirements-prod.txt` includes all dependencies
4. Check Python version matches (`3.11.0`)

### Slow Backend Response (Render Free Tier)

**Symptom:** First request takes 30+ seconds

**Solution:**
- Render's free tier spins down after 15 minutes of inactivity
- First request "wakes up" the service (cold start)
- Consider upgrading to a paid plan for always-on service
- Implement a cron job to ping `/health` every 10 minutes

---

## Environment Variables Reference

### Backend (Render)

```bash
JWT_SECRET_KEY=your-super-secret-key-123
SUPABASE_URL=https://kquhgkomsqlbqjigxmiz.supabase.co
SUPABASE_KEY=eyJhbGci...
CORS_ALLOWED_ORIGINS=https://ai-skill-gap-generator.vercel.app
PYTHON_VERSION=3.11.0
```

### Frontend (Vercel)

```bash
VITE_API_URL=https://ai-skill-gap-generator.onrender.com
VITE_SUPABASE_URL=https://kquhgkomsqlbqjigxmiz.supabase.co
VITE_SUPABASE_KEY=eyJhbGci...
```

---

## Updating Deployment

### Backend Updates

1. Push changes to GitHub `main` branch
2. Render automatically rebuilds and redeploys
3. Monitor deployment in Render dashboard

### Frontend Updates

1. Push changes to GitHub `main` branch
2. Vercel automatically rebuilds and redeploys
3. Monitor deployment in Vercel dashboard

---

## Security Best Practices

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong JWT secrets** - Generate with `openssl rand -hex 32`
3. **Restrict CORS origins** - Never use `*` in production
4. **Rotate Supabase keys** - If accidentally exposed
5. **Enable Vercel password protection** - For staging deployments
6. **Monitor Render logs** - Check for suspicious activity

---

## Cost Optimization

### Render Free Tier Limits
- 750 hours/month (enough for one always-on service)
- Spins down after 15 minutes of inactivity
- 512 MB RAM

### Vercel Free Tier Limits
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS

### Supabase Free Tier Limits
- 500 MB database storage
- 2 GB bandwidth/month
- 50,000 monthly active users

---

## Next Steps

1. ✅ Set up custom domain (optional)
2. ✅ Configure analytics (Vercel Analytics, Google Analytics)
3. ✅ Set up error monitoring (Sentry, LogRocket)
4. ✅ Implement CI/CD tests
5. ✅ Add staging environment

---

## Support

If you encounter issues not covered in this guide:

1. Check Render logs: https://dashboard.render.com → Your Service → Logs
2. Check Vercel logs: https://vercel.com/dashboard → Your Project → Deployments → Logs
3. Review browser console for frontend errors
4. Verify all environment variables are set correctly
