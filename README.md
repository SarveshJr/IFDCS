# IFDCS — Industrial Fire Detection & Classification System

**Smart India Hackathon 2026**  
**Problem Statement ID:** SIH26162  
**Problem Statement:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data  
**Theme:** Disaster Management  
**Team ID:** SIH26-A0H-T316  
**Team Name:** HACK PROCESSING UNIT  

---

## 📌 Project Overview
Industrial facilities generate thermal signatures that can be observed from space, but conventional satellite systems (like NASA FIRMS) cannot distinguish industrial fires from gas flares, wildfires, mining, and agricultural burning. 

**IFDCS** provides an end-to-end AI-enabled geospatial system that automatically ingests spaceborne thermal observations, cross-references with land-cover classification and industrial registries, and provides explainable AI (SHAP) alerts to disaster response teams and facility operators.

---

## 🚀 Frontend Architecture & Setup

The dashboard is built with:
- **React 19 + TypeScript + Vite**
- **Tailwind CSS v4**
- **Leaflet & React-Leaflet** (GIS mapping restricted to India & South Asia)
- **Recharts** (90-day facility thermal baselines)
- **NASA FIRMS Live API Proxy** (VIIRS SNPP 375m near-real-time ingestion)
- **Zustand** (State management)
- **Lucide React** (Icons)

### Getting Started

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start local development server
npm run dev
```

Visit `http://localhost:5173/` in your browser.
