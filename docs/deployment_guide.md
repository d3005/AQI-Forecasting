# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Real-Time AQI Prediction System to Railway. Railway offers a streamlined deployment experience with built-in PostgreSQL support and automatic HTTPS.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Account**: For repository connection
3. **OpenWeatherMap API Key**: Get from [openweathermap.org/api](https://openweathermap.org/api)

## Project Structure

Ensure your repository has the following structure:

```
AQI_Index/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   └── ml/
│   ├── requirements.txt
│   ├── Procfile
│   └── railway.toml
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── railway.toml
└── docs/
```

## Step 1: Create Railway Project

1. Log in to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your repository
5. Select the `AQI_Index` repository

## Step 2: Configure PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "Add PostgreSQL"**
3. Railway will automatically provision a PostgreSQL instance
4. Click on the PostgreSQL service to view connection details
5. Copy the `DATABASE_URL` (it will look like: `postgresql://postgres:xxx@xxx.railway.internal:5432/railway`)

## Step 3: Deploy Backend Service

### 3.1 Create Backend Service

1. Click **"+ New" → "GitHub Repo"**
2. Select your repository
3. Configure the service:
   - **Root Directory**: `backend`
   - **Watch Path**: `backend/**`

### 3.2 Configure Environment Variables

In the backend service settings, add these variables:

| Variable | Value | Required |
|----------|-------|----------|
| `DATABASE_URL` | Copy from PostgreSQL service | ✅ |
| `OPENWEATHERMAP_API_KEY` | Your API key | ✅ |
| `SECRET_KEY` | Generate a random string | ✅ |
| `CORS_ORIGINS` | `https://your-frontend.up.railway.app` | ✅ |
| `DEBUG` | `false` | ✅ |
| `AQICN_API_TOKEN` | Optional backup API token | ❌ |
| `DATA_FETCH_INTERVAL_MINUTES` | `15` | ❌ |
| `MODEL_RETRAIN_INTERVAL_HOURS` | `24` | ❌ |
| `DEFAULT_CITY` | `Delhi` | ❌ |
| `DEFAULT_COUNTRY` | `India` | ❌ |
| `DEFAULT_LATITUDE` | `28.6139` | ❌ |
| `DEFAULT_LONGITUDE` | `77.2090` | ❌ |

**Important**: For `DATABASE_URL`, modify the URL from PostgreSQL:
- Change `postgresql://` to `postgresql+asyncpg://`
- If using internal networking, use the internal URL

Example:
```
# From Railway PostgreSQL
postgresql://postgres:xxx@containers-xxx.railway.internal:6969/railway

# Your DATABASE_URL
postgresql+asyncpg://postgres:xxx@containers-xxx.railway.internal:6969/railway
```

### 3.3 Generate Domain

1. Go to **Settings → Networking**
2. Click **"Generate Domain"**
3. Note the URL (e.g., `aqi-backend.up.railway.app`)

## Step 4: Deploy Frontend Service

### 4.1 Create Frontend Service

1. Click **"+ New" → "GitHub Repo"**
2. Select your repository
3. Configure the service:
   - **Root Directory**: `frontend`
   - **Watch Path**: `frontend/**`

### 4.2 Configure Environment Variables

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend.up.railway.app` |
| `VITE_WS_URL` | `wss://your-backend.up.railway.app` |

### 4.3 Generate Domain

1. Go to **Settings → Networking**
2. Click **"Generate Domain"**
3. Note the URL (e.g., `aqi-dashboard.up.railway.app`)

### 4.4 Update Backend CORS

Go back to the backend service and update `CORS_ORIGINS`:
```
https://aqi-dashboard.up.railway.app
```

## Step 5: Verify Deployment

### 5.1 Check Backend Health

Visit: `https://your-backend.up.railway.app/health`

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "scheduler_running": true
}
```

### 5.2 Check API Documentation

Visit: `https://your-backend.up.railway.app/docs`

You should see the FastAPI Swagger documentation.

### 5.3 Check Frontend

Visit: `https://your-frontend.up.railway.app`

You should see the AQI Dashboard with real-time data.

## Step 6: Monitor & Troubleshoot

### View Logs

1. Click on a service in Railway
2. Go to the **"Logs"** tab
3. View real-time logs

### Common Issues

#### Database Connection Failed
- Verify `DATABASE_URL` uses `postgresql+asyncpg://`
- Check if PostgreSQL service is running
- Verify internal networking is enabled

#### API Key Errors
- Check `OPENWEATHERMAP_API_KEY` is correctly set
- Verify API key is active at openweathermap.org

#### CORS Errors
- Ensure frontend URL is in `CORS_ORIGINS`
- Include `https://` in the URL

#### WebSocket Connection Failed
- Verify `VITE_WS_URL` uses `wss://` (not `ws://`)
- Check backend is accepting WebSocket connections

## Step 7: Custom Domain (Optional)

### Configure Custom Domain

1. Go to service **Settings → Networking**
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `aqi.yourdomain.com`)
4. Add the CNAME record in your DNS provider:
   ```
   Type: CNAME
   Name: aqi
   Value: your-service.up.railway.app
   ```
5. Wait for DNS propagation

### Update Environment Variables

After setting custom domain, update:
- Backend `CORS_ORIGINS` with new frontend URL
- Frontend `VITE_API_URL` and `VITE_WS_URL` with new backend URL

## Architecture on Railway

```
┌─────────────────────────────────────────────────────────────────┐
│                      Railway Project                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │    Backend      │  │   Frontend      │ │
│  │   (Database)    │  │   (FastAPI)     │  │   (React+Vite)  │ │
│  │                 │  │                 │  │                 │ │
│  │ Railway Plugin  │  │ Root: /backend  │  │ Root: /frontend │ │
│  │                 │  │                 │  │                 │ │
│  │ Internal URL:   │  │ Domain:         │  │ Domain:         │ │
│  │ containers-xxx  │  │ aqi-backend     │  │ aqi-dashboard   │ │
│  │ .railway.internal│ │ .up.railway.app │  │ .up.railway.app │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│          │                    │                    │            │
│          └────────────────────┼────────────────────┘            │
│                    Internal Network                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Cost Estimation

Railway's pricing (as of 2024):
- **Hobby Plan**: $5/month includes $5 usage credits
- **Pro Plan**: $20/month includes $20 usage credits

Estimated monthly usage:
- PostgreSQL: ~$3-5
- Backend: ~$5-10 (depends on traffic)
- Frontend: ~$2-3 (static hosting)

**Total**: ~$10-20/month

## Security Checklist

- [ ] Use HTTPS for all endpoints
- [ ] Set strong `SECRET_KEY`
- [ ] Never commit `.env` files
- [ ] Enable Railway private networking
- [ ] Review CORS settings
- [ ] Set `DEBUG=false` in production

## Maintenance

### Automatic Updates
Railway automatically redeploys when you push to your GitHub repository.

### Manual Redeploy
1. Go to service settings
2. Click **"Redeploy"**

### Database Backups
Railway PostgreSQL includes automatic backups. To export:
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Scaling
To handle more traffic:
1. Go to service settings
2. Adjust **Replicas** count
3. Configure **Health Checks**

---

## Quick Reference

| Service | URL Pattern |
|---------|-------------|
| Backend API | `https://your-backend.up.railway.app/api/v1/` |
| API Docs | `https://your-backend.up.railway.app/docs` |
| Health Check | `https://your-backend.up.railway.app/health` |
| WebSocket | `wss://your-backend.up.railway.app/ws/aqi/{id}` |
| Frontend | `https://your-frontend.up.railway.app` |
