# 🚀 Quick Deployment Reference

## Environment Variables to Set

### 📦 Render (Backend)
Go to: https://dashboard.render.com → Your Service → Environment

```bash
JWT_SECRET_KEY=your-super-secret-key-123
SUPABASE_URL=https://kquhgkomsqlbqjigxmiz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtxdWhna29tc3FsYnFqaWd4bWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3NTMzMzYsImV4cCI6MjA4MjMyOTMzNn0.6xEz_PNVy_--IdQ-QnbiLqf2FzjOIyOEXbBQx6KDY0s
CORS_ALLOWED_ORIGINS=https://ai-skill-gap-generator.vercel.app
```

### 🌐 Vercel (Frontend)
Go to: https://vercel.com/dashboard → Your Project → Settings → Environment Variables

```bash
VITE_API_URL=https://ai-skill-gap-generator.onrender.com
VITE_SUPABASE_URL=https://kquhgkomsqlbqjigxmiz.supabase.co
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtxdWhna29tc3FsYnFqaWd4bWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3NTMzMzYsImV4cCI6MjA4MjMyOTMzNn0.6xEz_PNVy_--IdQ-QnbiLqf2FzjOIyOEXbBQx6KDY0s
```

---

## 🔧 Critical Steps After Setting Variables

### Render
1. Set all 4 environment variables above
2. Click **"Save Changes"**
3. Click **"Manual Deploy"** → **"Deploy latest commit"**
4. Wait 5-10 minutes for build
5. Test: `curl https://ai-skill-gap-generator.onrender.com/health`

### Vercel
1. Set all 3 environment variables above
2. Select **"Production, Preview, Development"** for each
3. Click **"Save"**
4. Go to **"Deployments"** tab
5. Click **"Redeploy"** on latest deployment
6. Wait 2-5 minutes for build
7. Visit: https://ai-skill-gap-generator.vercel.app

---

## ✅ Verification Checklist

After deployment, check:

- [ ] Backend health endpoint returns 200: https://ai-skill-gap-generator.onrender.com/health
- [ ] Frontend loads without console errors
- [ ] No "Supabase credentials not configured" warning
- [ ] No CORS errors in browser console
- [ ] Can sign in / sign up
- [ ] Can upload resume
- [ ] Skills are extracted and displayed
- [ ] Can generate learning path

---

## 🐛 Common Issues

### CORS Error
**Fix:** Verify `CORS_ALLOWED_ORIGINS` in Render is exactly `https://ai-skill-gap-generator.vercel.app` (no trailing slash)

### Supabase Warning
**Fix:** Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_KEY` are set in Vercel

### 404 on API Calls
**Fix:** Verify `VITE_API_URL` in Vercel is `https://ai-skill-gap-generator.onrender.com`

### Backend Not Responding
**Fix:** Render free tier spins down after 15 min. First request takes 30+ seconds to wake up.

---

## 📝 Important Notes

⚠️ **Backend uses `SUPABASE_URL` (no VITE_ prefix)**
⚠️ **Frontend uses `VITE_SUPABASE_URL` (with VITE_ prefix)**
⚠️ **Always redeploy after changing environment variables**
⚠️ **Render free tier has cold starts (first request is slow)**

---

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
