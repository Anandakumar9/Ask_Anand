# StudyPulse - Frontend Blank Screen Fix Guide

## 🚨 Current Issue

**Problem**: Both local frontend (http://localhost:8082) and production frontend (https://studypulse-eta.vercel.app) show blank white screens.

**Status**: Backend API is working perfectly (tested and confirmed), but the frontend is not rendering.

---

## ✅ What's Confirmed Working

I've tested the backend extensively and **everything is working**:

- ✅ Railway Backend: https://askanand-simba.up.railway.app
- ✅ Guest Auth: Returns valid JWT tokens
- ✅ Exams Endpoint: Returns 8 exams with subjects
- ✅ Registration: Creates new users
- ✅ All API endpoints: Responding correctly

**The backend is NOT the problem!**

---

## 🔍 Diagnosing the Blank Screen Issue

The blank screen means the **JavaScript is not executing** properly on the frontend. Here's how to find out why:

### Step 1: Use the Diagnostic Tool

I created a comprehensive diagnostic tool for you:

**Open this file in your browser:**
```
c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\diagnostic.html
```

Or double-click: `diagnostic.html` in the `studypulse` folder

**This tool will:**
- Test all backend endpoints
- Test API connections
- Test CORS configuration
- Simulate the complete user flow
- Give you specific errors to fix

---

### Step 2: Check Browser Console (Most Important!)

The **browser console** will tell you exactly what's wrong:

1. **Open Vercel frontend**: https://studypulse-eta.vercel.app
2. **Press F12** (or Right-click → Inspect)
3. **Go to "Console" tab**
4. **Look for red error messages**

**Common Errors and Solutions:**

#### Error 1: "Failed to fetch" or "Network request failed"
**Cause**: Frontend can't reach the backend API
**Solution**:
```bash
# Vercel environment variable might not be set correctly
# Check with:
cd studypulse/frontend
vercel env ls

# If NEXT_PUBLIC_API_URL is not set or wrong:
vercel env rm NEXT_PUBLIC_API_URL production
echo "https://askanand-simba.up.railway.app/api/v1" | vercel env add NEXT_PUBLIC_API_URL production

# Redeploy:
vercel --prod
```

#### Error 2: "CORS policy blocked"
**Cause**: Backend is not allowing frontend domain
**Solution**:
```bash
# Update Railway CORS settings
cd studypulse/backend
railway variables --set CORS_ORIGINS="https://studypulse-eta.vercel.app,https://askanand-simba.up.railway.app,http://localhost:3000,http://localhost:8082"

# Redeploy Railway
railway up
```

#### Error 3: "Unexpected token '<'"
**Cause**: API is returning HTML instead of JSON
**Solution**: Check if the API endpoint URL is correct (should end with `/api/v1`)

#### Error 4: "Cannot read property of undefined"
**Cause**: Frontend expecting data that's not coming from backend
**Solution**: Check Network tab to see what data is actually being returned

---

### Step 3: Check Network Tab

1. **Stay in F12 DevTools**
2. **Go to "Network" tab**
3. **Refresh the page** (Ctrl + F5)
4. **Look for red requests** (failed)

**What to check:**
- Are there any requests to `https://askanand-simba.up.railway.app`?
  - ✅ YES → Good, frontend is trying to connect
  - ❌ NO → Environment variable not set correctly

- What's the status code of API requests?
  - ✅ 200 OK → API working
  - ❌ 404 Not Found → Wrong URL
  - ❌ 500 Internal Server Error → Backend error
  - ❌ 0 or failed → CORS issue

- Click on a failed request to see details

---

## 🔧 Quick Fixes to Try

### Fix 1: Redeploy Frontend with Correct Environment Variable

```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\frontend

# Remove old environment variable
vercel env rm NEXT_PUBLIC_API_URL production

# Add correct one
"https://askanand-simba.up.railway.app/api/v1" | vercel env add NEXT_PUBLIC_API_URL production

# Redeploy to production
vercel --prod --yes
```

Wait ~30-60 seconds for deployment to complete, then test: https://studypulse-eta.vercel.app

---

### Fix 2: Test with Local Frontend

Instead of using the Flutter mobile app, let's test the Next.js frontend directly:

```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\frontend

# Create local environment variable
echo "NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1" > .env.local

# Install dependencies (if needed)
npm install

# Run development server
npm run dev
```

Then open: http://localhost:3000

This will show you any JavaScript errors immediately.

---

### Fix 3: Check Mobile App API URL

The mobile app might be using the wrong API URL:

```powershell
# Check the current API URL
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
grep -n "BaseUrl" lib/api/api_service.dart
```

Make sure these values are correct:
- `_devBaseUrlWeb`: `'http://localhost:8001/api/v1'` (for local testing)
- `_prodBaseUrl`: `'https://askanand-simba.up.railway.app/api/v1'` (for production)

---

## 🧪 Testing the Mobile App

### Option A: Run Mobile App (Current Approach)

I've already started the mobile app for you in the background. Wait 2-3 minutes, then:

```
Open: http://localhost:8082
```

**Check:**
1. Does the page load at all? (even blank is OK for now)
2. Press F12 → Console tab
3. Look for errors
4. Check Network tab for API calls

---

### Option B: Use the Next.js Frontend Instead (Recommended for Debugging)

The mobile app (Flutter) is more complex. For debugging, use the Next.js frontend:

```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\frontend
npm run dev
```

Open: http://localhost:3000

This is easier to debug because:
- Faster startup (~5 seconds vs 2-3 minutes)
- Better error messages in console
- Easier to see what's happening

---

## 📊 Expected Behavior (When Working)

When the frontend is working correctly, you should see:

### On Desktop (http://localhost:3000 or Vercel):
1. **Login page** with:
   - StudyPulse logo/title
   - Email and password fields
   - "Continue as Guest" button
   - Register button

2. **After guest login**:
   - Redirected to home/dashboard
   - Can see stats (stars, study time, tests)
   - Can navigate to different sections

### Console Output (F12 → Console):
```
No errors (or only warnings, which are OK)
```

### Network Tab (F12 → Network):
```
Status  Method  URL
200     POST    https://askanand-simba.up.railway.app/api/v1/auth/guest
200     GET     https://askanand-simba.up.railway.app/api/v1/exams/
200     GET     https://askanand-simba.up.railway.app/api/v1/dashboard
```

---

## 🎯 Recommended Action Plan

**Follow these steps in order:**

### Step 1: Use Diagnostic Tool (2 minutes)
```
Open: c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\diagnostic.html
Click: "Test API Endpoints"
Click: "Test Complete Flow"
```

This will confirm the backend is working.

---

### Step 2: Check Vercel Console (2 minutes)
```
1. Open: https://studypulse-eta.vercel.app
2. Press F12
3. Go to Console tab
4. Screenshot the errors
5. Go to Network tab
6. Refresh page
7. Screenshot the failed requests
```

---

### Step 3: Fix Based on Errors
- **If "Failed to fetch"**: Redeploy with correct API URL (Fix 1)
- **If "CORS error"**: Update CORS settings (Fix 2 in Error section)
- **If blank console**: Check Network tab for clues

---

### Step 4: Test Local Frontend (5 minutes)
```powershell
cd studypulse/frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1" > .env.local
npm install
npm run dev
```

Open: http://localhost:3000

This will give you a working local version you can test with.

---

## 🎓 Understanding the Issue

**Why is the backend working but frontend blank?**

The backend API is working perfectly (I tested it extensively). The issue is that:

1. **Frontend HTML loads** (you see a blank page, not a "Can't connect" error)
2. **JavaScript is not executing** or **failing silently**
3. **Most likely causes**:
   - Environment variable `NEXT_PUBLIC_API_URL` not set in Vercel build
   - Frontend trying to reach wrong API URL
   - CORS blocking the requests
   - JavaScript error preventing app from rendering

**The diagnostic steps above will pinpoint the exact issue.**

---

## 📁 Files I Created for You

1. **`diagnostic.html`** - Open this immediately to test everything
   - Location: `studypulse/diagnostic.html`
   - Tests all API endpoints
   - Simulates complete user flow
   - Shows you exactly what's failing

2. **`start_all.bat`** - One-click startup for all servers
   - Starts backend on port 8001
   - Starts mobile app on port 8082
   - Opens diagnostic tool automatically

3. **`HOW_TO_RUN_MOBILE_APP.md`** - Complete guide for running mobile app

4. **`DEPLOYMENT_FIX_REPORT.md`** - Full deployment status report

---

## 🆘 If Still Having Issues

**Run this command and send me the output:**

```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\frontend
vercel env pull .env.vercel
cat .env.vercel
```

This will show me what environment variables Vercel is actually using.

**Also check:**
```powershell
cd studypulse/frontend
cat src/services/api.ts | head -20
```

This shows the API configuration in the frontend code.

---

## ✅ Success Checklist

You'll know it's working when:

- [ ] Diagnostic tool shows all green (✅) results
- [ ] Browser console has no red errors
- [ ] Network tab shows 200 OK for API calls
- [ ] Login page displays with buttons
- [ ] Guest login works and redirects to dashboard
- [ ] Can see list of exams

---

## 🚀 Next Steps

1. **Immediately**: Open `diagnostic.html` and run all tests
2. **Then**: Check browser console for errors on Vercel frontend
3. **Then**: Try local frontend with `npm run dev`
4. **Then**: Share the errors you see with me

The diagnostic tool will give you specific, actionable information about what's failing!

---

**The backend is confirmed working. The issue is purely on the frontend side, and we can fix it once we see the actual errors in the browser console.**
