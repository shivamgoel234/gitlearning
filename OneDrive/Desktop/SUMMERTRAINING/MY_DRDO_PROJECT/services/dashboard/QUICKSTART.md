# Dashboard Service - Quick Start Guide

## ⚡ 3-Step Quickstart

### Step 1: Install Dependencies
```bash
cd services/dashboard
pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Configure Services
Edit `.env` and set your microservice URLs:
```bash
ALERT_SERVICE_URL=http://localhost:8003
ML_SERVICE_URL=http://localhost:8002
```

### Step 3: Run Dashboard
```bash
streamlit run app/main.py
```

Dashboard opens at: **http://localhost:8004**

---

## 🎯 What You'll See

When the dashboard loads, you'll see:

### 1. **Metrics Row** (Top)
- 🔔 Total Alerts
- 🔴 Critical Count
- 🟠 High Priority Count
- 📊 Average Failure Risk

### 2. **Visualizations** (Middle)
- **Pie Chart**: Severity distribution
- **Bar Chart**: Top 10 equipment by risk
- **Scatter Plot**: Risk vs time to failure

### 3. **Active Alerts Table** (Bottom)
- List of all active alerts
- Color-coded by severity
- Shows equipment ID, risk, days until failure

### 4. **Service Status** (Footer)
- ✅ Alert Service Connected
- ✅ ML Service Connected
- 📡 Last update time

---

## 🔄 Using the Dashboard

### Manual Refresh
Click **"🔄 Refresh Now"** in the sidebar to reload data

### Clear Cache
Click **"🗑️ Clear Cache"** to clear all cached data

### View Debug Info
Expand **"🔧 Debug Information"** at the bottom to see:
- Total alerts count
- Service health status
- Configuration settings

---

## ✅ Testing Checklist

Before deploying, verify:

- [ ] Dashboard loads without errors
- [ ] All 4 metrics display correctly
- [ ] 3 charts render properly
- [ ] Active alerts table shows data
- [ ] "Alert Service Connected" shows ✅
- [ ] Refresh button works
- [ ] Service health indicators are accurate

---

## 🐛 Common Issues

### Problem: "No active alerts" message
**Solution:** 
1. Check if Alert service is running: `curl http://localhost:8003/health`
2. Generate some alerts using the Alert service
3. Click "Refresh Now"

### Problem: "Alert Service Disconnected"
**Solution:**
1. Verify `ALERT_SERVICE_URL` in `.env`
2. Ensure Alert service is running on port 8003
3. Test connection: `curl http://localhost:8003/health`

### Problem: Charts not displaying
**Solution:**
1. Check browser console for errors
2. Verify Plotly is installed: `pip list | grep plotly`
3. Clear cache and refresh

### Problem: Dashboard loads slowly
**Solution:**
1. Reduce `MAX_ALERTS_DISPLAY` in `.env` (default: 50)
2. Increase `CACHE_TTL` (default: 30 seconds)
3. Check Alert service response time

---

## 📦 Docker Quick Start

### Build and Run
```bash
cd services/dashboard

# Build image
docker build -t drdo-dashboard .

# Run container
docker run -p 8004:8004 --env-file .env drdo-dashboard
```

### Access Dashboard
Open: **http://localhost:8004**

---

## 🔗 Integration Test

### Full System Test Flow

1. **Start Alert Service** (Port 8003)
   ```bash
   cd services/alert-maintenance
   uvicorn app.main:app --port 8003
   ```

2. **Generate Test Alerts**
   ```bash
   curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95.5&vibration=0.85&pressure=4.2"
   ```

3. **Start Dashboard** (Port 8004)
   ```bash
   cd services/dashboard
   streamlit run app/main.py
   ```

4. **Verify Dashboard**
   - Open http://localhost:8004
   - Check metrics show > 0 alerts
   - Verify charts display data
   - Check table shows the alert

---

## 🎨 Dashboard Features

### Essential Features (Included)
✅ Real-time metrics display  
✅ Interactive Plotly charts  
✅ Data table with color coding  
✅ Manual refresh control  
✅ Service health monitoring  
✅ Cached data (30 seconds)  
✅ Responsive layout  

### Not Included (By Design)
❌ Auto-refresh (use manual refresh)  
❌ Authentication (demo only)  
❌ Export to CSV/PDF  
❌ Advanced filtering  
❌ Historical data view  
❌ Multiple pages  

---

## 📊 Sample Data

For testing, you can use these curl commands to generate sample alerts:

```bash
# Critical Alert
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95&vibration=0.85&pressure=4.5"

# High Priority Alert
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=AIRCRAFT-042&temperature=88&vibration=0.65&pressure=3.8"

# Medium Alert (may not create alert - threshold dependent)
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=NAVAL-003&temperature=70&vibration=0.50&pressure=3.0"
```

Then refresh the dashboard to see the new alerts!

---

## 🚀 Production Deployment

### Before deploying to production:

1. ✅ Update `.env` with production service URLs
2. ✅ Enable authentication (not included in MVP)
3. ✅ Set `CACHE_TTL` based on your needs
4. ✅ Configure proper logging
5. ✅ Set up monitoring/alerting
6. ✅ Use HTTPS for all API calls
7. ✅ Review security settings in `.streamlit/config.toml`

---

## 📞 Need Help?

1. Check logs: `streamlit run app/main.py --logger.level=debug`
2. Review README.md for detailed documentation
3. Check service health endpoints
4. Verify .env configuration
5. Look at Debug Information in dashboard

---

**Dashboard Version:** 1.0.0  
**Port:** 8004  
**Status:** ✅ MVP Ready

**Next Steps:** 
1. Start the Alert service
2. Generate some test alerts
3. Run the dashboard
4. Enjoy real-time monitoring! 🎉
