# NAVIQ — SIH26006 Intelligent Freight Forecasting, Vessel Chartering & Bulk Cargo Procurement Platform

A Next.js 14, TypeScript, and Tailwind CSS frontend application built for the **SIH26006 Maritime Intelligence Platform**. Integrates with Python FastAPI backends, PostgreSQL/PostGIS, AIS live vessel telemetry, ML freight forecasting models with confidence bands, spatial port congestion prediction, and multi-objective vessel charter optimization.

---

## 🌟 Core Features & Highlights

### 1. Decision-Centric Architecture (`<DecisionRecommendation />`)
Directly answers the three fundamental questions for maritime procurement:
1. **WHICH VESSEL TO CHARTER?** (Ranked match scores, DWT capacity, draft suitability, ballast distance)
2. **WHEN TO CHARTER IT?** (ML timing strategy: **WAIT 3 DAYS** vs **BOOK NOW**)
3. **WHAT WILL IT COST?** (Expected freight $/MT, potential savings, and voyage cost breakdown)

### 2. End-to-End Golden User Flow
$$\text{Cargo Requirement (75k MT Coal)} \longrightarrow \text{Vessel Matching} \longrightarrow \text{AIS + Port Analysis} \longrightarrow \text{ML Freight Forecast} \longrightarrow \text{Congestion Forecast} \longrightarrow \text{AI Optimization} \longrightarrow \text{Charter Contract Execution} \longrightarrow \text{Voyage Tracking}$$

### 3. Dynamic Role-Based Dashboards
- **Procurement Officer** (`/dashboard/procurement`): Bulk cargo tenders, AI charter decision engine, multi-vessel comparison, estimated cost savings.
- **Ship Owner** (`/dashboard/ship-owner`): Fleet overview, cargo opportunity marketplace, tender bids, voyage revenue tracking.
- **Port Owner** (`/dashboard/port-owner`): Live berth status (CB-1, CB-2, etc.), anchorage queue, port utilization %, and 7-day congestion forecast.
- **System Admin** (`/dashboard/admin`): Global system telemetry, AI inference latency, active fleets, and security monitoring.

### 4. Machine Learning & Spatial Intelligence
- **ML Freight Forecaster** (`/forecasts`): Probabilistic deep learning model visualizing actual rates vs. predicted curves with an **87% confidence interval band**.
- **Spatial Port Congestion** (`/congestion`): 7-day anchorage waiting time forecast and queue sequencing.
- **Interactive AIS & GIS Nautical Map** (`/vessels`): Dark nautical CartoDB tiles, vessel heading rotation, route polylines, and Under Keel Clearance (UKC) bathymetry safety checks.
- **Explainable AI (XAI)**: Context-aware dynamic rationale for every AI charter recommendation.

### 5. Live Backend Integration + High-Fidelity Demo Simulation
- **Centralized API Client** (`lib/api.ts`): Ready for FastAPI at `http://localhost:8000/api/v1` with JWT interceptors.
- **Zero-Breakage Demo Engine**: Prominent **"● LIVE API / ⚡ DEMO SIMULATION"** toggle in the top bar ensures judges experience all features regardless of whether the Python backend is active.

---

## 🚀 Getting Started

### Prerequisites
- Node.js LTS (v20+ or v22+)
- npm or pnpm / yarn

### Installation & Running

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies (if not already installed)
npm install

# 3. Start the Next.js development server
npm run dev

# 4. Open in browser
http://localhost:3000
```

### Building for Production

```bash
npm run build
npm start
```

---

## 📁 Directory Structure

```
frontend/
├── app/
│   ├── (auth)/login & register        # Authentication & 1-click role quick logins
│   ├── dashboard/                     # Role-specific dashboards (procurement, ship-owner, port-owner, admin)
│   ├── cargo/                         # Bulk cargo requirements & marketplace tenders
│   ├── vessels/                       # AIS fleet directory, vessel detail & matching
│   ├── forecasts/                     # ML freight forecasting with confidence bands
│   ├── congestion/                    # Port congestion & waiting time predictions
│   ├── optimization/                  # AI charter optimization & cost breakdowns
│   ├── charters/                      # Charter contracts, offers & comparison matrix
│   ├── voyages/                       # Live voyage tracking & milestone timeline
│   ├── ports/                         # Port infrastructure & bathymetry limits
│   ├── market/                        # Baltic Dry Index, bunker fuel & commodities
│   └── notifications/                 # Real-time maritime notification hub
│
├── components/
│   ├── dashboard/DecisionRecommendation.tsx  # Core AI Decision Component
│   ├── charts/FreightForecastChart.tsx       # Recharts Line + Area Confidence Band
│   ├── maps/AisVesselMap.tsx                 # Leaflet Dark Nautical AIS GIS Map
│   ├── cargo/CargoRequirementForm.tsx        # React Hook Form + Zod Bulk Cargo Form
│   └── ui/                                   # Reusable UI component library
│
├── lib/
│   ├── api.ts                         # Axios client with JWT interceptor & smart demo fallback
│   ├── auth.tsx                       # AuthContext & role protection
│   ├── websocket.ts                   # WebSocket client for AIS telemetry
│   └── demoData.ts                    # High-fidelity realistic simulation dataset
│
└── services/                          # Domain API service modules
```
