# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Real-Time AQI Prediction System using:
- **Frontend**: Vercel (React)
- **Backend**: Railway (FastAPI)
- **Database**: Firebase Realtime Database

---

## Live Deployment URLs

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | https://aqi-forecasting-index.vercel.app |
| Backend | Railway | https://aqi-forecasting-production.up.railway.app |
| Database | Firebase | Realtime Database |

---

## Prerequisites

1. **GitHub Account**: For repository connection
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
3. **Railway Account**: Sign up at [railway.app](https://railway.app)
4. **Firebase Project**: Create at [console.firebase.google.com](https://console.firebase.google.com)
5. **API Keys**:
   - WAQI: [aqicn.org/data-platform/token](https://aqicn.org/data-platform/token)
   - Ambee: [api.ambee.com](https://api.ambee.com)
   - OpenWeatherMap: [openweathermap.org/api](https://openweathermap.org/api)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Firebase      │  │    Railway      │  │     Vercel      │ │
│  │   (Database)    │  │   (Backend)     │  │   (Frontend)    │ │
│  │                 │  │                 │  │                 │ │
│  │ Realtime DB     │  │ FastAPI + ML    │  │ React App       │ │
│  │ Authentication  │  │ GA-KELM Model   │  │ Dashboard       │ │
│  │                 │  │ Scheduler       │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│          │                    │                    │            │
│          └────────────────────┼────────────────────┘            │
│                    HTTPS / REST                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Firebase Setup

### 1.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add project"**
3. Enter project name: `aqi-forecasting`
4. Disable Google Analytics (optional)
5. Click **Create project**

### 1.2 Enable Realtime Database

1. In Firebase Console, go to **Build → Realtime Database**
2. Click **"Create Database"**
3. Choose location (e.g., `us-central1`)
4. Start in **test mode** (we'll secure later)
5. Copy the database URL: `https://your-project-default-rtdb.firebaseio.com`

### 1.3 Enable Google Authentication

1. Go to **Build → Authentication**
2. Click **"Get started"**
3. Go to **Sign-in method** tab
4. Enable **Google** provider
5. Enter your project support email
6. Click **Save**

### 1.4 Get Service Account Key

1. Go to **Project Settings → Service accounts**
2. Click **"Generate new private key"**
3. Download the JSON file
4. Convert to base64 (for Railway):

**PowerShell:**
```powershell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "path\to\serviceAccountKey.json" -Raw)))
```

**Linux/Mac:**
```bash
base64 -i path/to/serviceAccountKey.json
```

### 1.5 Get Web App Config

1. Go to **Project Settings → General**
2. Under "Your apps", click **Add app → Web**
3. Register app with name: `AQI Dashboard`
4. Copy the Firebase config object

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Log in to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your repository
5. Select the `AQI-Forecasting` repository

### 2.2 Configure Deployment

Railway will detect the Dockerfile in the root directory. Verify:
- **Builder**: Dockerfile
- **Dockerfile Path**: `Dockerfile`

### 2.3 Set Environment Variables

In Railway service settings, add these variables:

| Variable | Value | Required |
|----------|-------|----------|
| `FIREBASE_URL` | `https://your-project-default-rtdb.firebaseio.com` | ✅ |
| `FIREBASE_CREDENTIALS` | Base64-encoded service account JSON | ✅ |
| `WAQI_API_KEY` | Your WAQI API token | ✅ |
| `AMBEE_API_KEY` | Your Ambee API key | ✅ |
| `API_KEY` | Your OpenWeatherMap API key | ✅ |
| `FRONTEND_URL` | `https://your-frontend.vercel.app` | ✅ |
| `LATITUDE` | Default latitude (e.g., `15.5057`) | ❌ |
| `LONGITUDE` | Default longitude (e.g., `80.0499`) | ❌ |

### 2.4 Generate Domain

1. Go to **Settings → Networking**
2. Click **"Generate Domain"**
3. Note the URL (e.g., `aqi-forecasting-production.up.railway.app`)

### 2.5 Verify Backend

Visit: `https://your-backend.up.railway.app/health`

Expected response:
```json
{
  "status": "healthy",
  "database": true,
  "model_trained": true,
  "scheduler_running": true
}
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Import Project

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New → Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `AQI-RealTime-System/frontend`

### 3.2 Set Environment Variables

| Variable | Value |
|----------|-------|
| `REACT_APP_API_URL` | `https://your-backend.up.railway.app` |

### 3.3 Deploy

Click **"Deploy"** and wait for build to complete.

### 3.4 Note Your Domain

After deployment, note your Vercel domain (e.g., `aqi-forecasting-index.vercel.app`)

---

## Step 4: Connect Everything

### 4.1 Update Railway FRONTEND_URL

Go back to Railway and update:
- `FRONTEND_URL` = `https://your-vercel-domain.vercel.app`

### 4.2 Add Vercel Domain to Firebase

1. Go to Firebase Console → **Authentication → Settings**
2. Under **Authorized domains**, click **"Add domain"**
3. Add: `your-vercel-domain.vercel.app`
4. Save

### 4.3 Verify End-to-End

1. Visit your Vercel frontend URL
2. Click **"Continue with Google"**
3. Sign in with your Google account
4. You should see the AQI Dashboard with live data

---

## Step 5: Configure EmailJS (Optional)

### 5.1 Create EmailJS Account

1. Sign up at [emailjs.com](https://www.emailjs.com)
2. Add Gmail as email service
3. Create email template with variables:
   - `{{email}}` - Recipient email
   - `{{user_name}}` - User name
   - `{{aqi}}` - Current AQI value
   - `{{location}}` - Location name
   - `{{category}}` - AQI category

### 5.2 Update AlertService

Edit `frontend/src/services/alertService.js`:
```javascript
const EMAILJS_SERVICE_ID = 'your_service_id';
const EMAILJS_TEMPLATE_ID = 'your_template_id';
const EMAILJS_PUBLIC_KEY = 'your_public_key';
```

---

## Troubleshooting

### Backend Issues

#### "Invalid JWT Signature" Error
- Re-generate Firebase service account key
- Ensure base64 encoding is correct
- Paste entire base64 string without line breaks

#### Database Connection Failed
- Verify `FIREBASE_URL` is correct
- Check Firebase Realtime Database is enabled
- Ensure service account has database access

#### CORS Errors
- Verify `FRONTEND_URL` matches your Vercel domain
- Include `https://` in the URL
- Redeploy backend after changing CORS settings

### Frontend Issues

#### "auth/unauthorized-domain" Error
- Add your Vercel domain to Firebase Authorized domains
- Wait a few minutes for propagation

#### API Data Not Loading
- Check `REACT_APP_API_URL` is set correctly
- Include `https://` in the URL
- Redeploy frontend after changing env variables

---

## Maintenance

### Automatic Updates
Both Vercel and Railway automatically redeploy when you push to GitHub.

### Manual Redeploy

**Railway:**
1. Go to service settings
2. Click **"Redeploy"**

**Vercel:**
1. Go to Deployments
2. Click ⋮ menu → **"Redeploy"**

### Viewing Logs

**Railway:** Click on service → **"Logs"** tab

**Vercel:** Deployments → Click deployment → **"Functions"** tab

---

## Security Checklist

- [x] Use HTTPS for all endpoints
- [x] Never commit credentials to git
- [x] Use environment variables for secrets
- [x] Enable Firebase security rules
- [x] Add only required domains to Firebase auth
- [x] Set `DEBUG=false` in production

---

## Cost Estimation

### Free Tier Limits

| Service | Free Tier |
|---------|-----------|
| Vercel | 100GB bandwidth/month |
| Railway | $5 credit/month |
| Firebase | 1GB database, 50k reads/day |
| WAQI | 1000 requests/day |
| Ambee | 10 requests/min |
| OpenWeatherMap | 1000 requests/day |
| EmailJS | 200 emails/month |

### Estimated Monthly Cost

For typical usage: **$0-5/month** (mostly free tier)

---

## Quick Reference

| Resource | URL |
|----------|-----|
| Frontend | https://aqi-forecasting-index.vercel.app |
| Backend API | https://aqi-forecasting-production.up.railway.app |
| Health Check | https://aqi-forecasting-production.up.railway.app/health |
| Current AQI | https://aqi-forecasting-production.up.railway.app/current |
| Prediction | https://aqi-forecasting-production.up.railway.app/predict |
