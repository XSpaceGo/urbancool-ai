# CoolGrid Mumbai

GeoAI-Based Urban Heat Mitigation and Cooling Strategy Optimizer for Mumbai.

This is a full-stack hackathon MVP that uses Google Earth Engine as the data engine, FastAPI for analysis, and React + Leaflet for the dashboard. It does not require manual dataset downloads, labels, or training masks. The app builds its own driver table by sampling Earth Engine rasters inside the Mumbai AOI.

## What It Does

- Automatically uses the Mumbai bounding box `[72.75, 18.85, 73.05, 19.30]`.
- Fetches Landsat 8/9 Collection 2 Level-2 imagery from Earth Engine.
- Computes NDVI, NDBI, LST in Celsius, built-up intensity, vegetation deficit, heat risk, and cooling priority.
- Fetches ERA5 daily air temperature, dewpoint, and wind vectors.
- Uses ESA WorldCover to identify water and green cover context.
- Samples driver points and trains a `scikit-learn` `RandomForestRegressor` to predict LST.
- Returns vegetation, built-up, and meteorology driver importance.
- Reports held-out R2, MAE, and RMSE for model validation.
- Simulates cooling strategies:
  - `+20%` vegetation
  - cool roof / `+0.15` albedo proxy
  - blue-green corridor priority
  - combined intervention
- Generates GEE map tiles for heat, risk, priority, and estimated cooling reduction.
- Produces top 10 intervention zones and a downloadable Markdown report.
- Optimizes the portfolio by maximum cooling and cooling per relative cost unit.

## Problem Statement Coverage

| Required outcome | UrbanCool AI implementation |
|---|---|
| Identify heat hotspots | Landsat LST, percentile statistics, hotspot mask, ranked 1 km grids |
| Heat stress mapping | Physics-weighted LST, NDBI, and inverse-NDVI heat risk raster |
| Quantify drivers | Random Forest feature and grouped importance |
| Atmospheric conditions | ERA5 air temperature, dewpoint-derived RH, and wind speed |
| Physics-informed AIML | Bounded ML sensitivity plus albedo, evapotranspiration, and water-proximity priors |
| Validate AIML | Held-out R2, MAE, and RMSE |
| Cooling scenarios | Greening, cool roof, blue-green corridor, and combined portfolio |
| Optimal strategy | Maximum cooling and cost-effectiveness selection |
| Spatial placement | Top 10 priority grids with coordinates and intervention type |
| Temperature reduction | Per-pixel and zonal estimated reduction in degrees Celsius |

## Project Structure

```text
backend/
  main.py
  gee_service.py
  ml_model.py
  requirements.txt
  .env.example
frontend/
  package.json
  index.html
  eslint.config.js
  src/
    App.jsx
    api.js
    styles.css
    components/
      MapView.jsx
      StatsCards.jsx
      DriverChart.jsx
      RecommendationPanel.jsx
      HotspotTable.jsx
```

## Google Earth Engine Authentication

Install the Earth Engine CLI in the backend environment, then authenticate:

```bash
earthengine authenticate
```

If your Google Cloud project is required by your account, copy the env example:

```bash
cd backend
cp .env.example .env
```

Set:

```text
GEE_PROJECT=your-google-cloud-project-id
```

For service account deployments, also set:

```text
GEE_SERVICE_ACCOUNT=service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=/path/to/key.json
```

Hosted deployments can store the complete service-account JSON as a secret instead:

```text
GEE_PRIVATE_KEY_JSON={"type":"service_account",...}
```

Never commit a password, OAuth credential file, or service-account JSON.

The Google account or service account must be registered for Google Earth Engine access.

## Run The Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Live Earth Engine credential/connectivity check:

```bash
curl "http://127.0.0.1:8000/health?deep=true"
```

Run analysis:

```bash
curl "http://127.0.0.1:8000/analyze?start=2024-03-01&end=2024-05-31"
```

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

If the backend is on a different URL, create `frontend/.env`:

```text
VITE_API_BASE=http://127.0.0.1:8000
```

## API Endpoints

- `GET /health`
- `GET /analyze?start=2024-03-01&end=2024-05-31`
- `GET /tiles/{layer}`
- `GET /report`

Valid tile layers:

- `lst`
- `heat_risk`
- `priority`
- `cooling_reduction`
- `hotspots`
- `ndvi`
- `ndbi`
- `greening_reduction`
- `cool_roof_reduction`
- `blue_green_reduction`

## Automated Tests

```bash
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend quality checks:

```bash
cd frontend
npm run lint
npm run build
```

The backend unit tests validate Random Forest learning, grouped driver importance, scenario scoring, and optimization without making live Earth Engine calls.

## Production Deployment

The root `Dockerfile` builds React and serves the compiled dashboard through FastAPI as one web service.

Local Docker run:

```bash
docker build -t urbancool-ai .
docker run --rm -p 8000:8000 --env-file backend/.env urbancool-ai
```

Open `http://127.0.0.1:8000`.

Render deployment:

1. Push this repository to GitHub.
2. In Render, create a Blueprint from `render.yaml`.
3. Add `GEE_SERVICE_ACCOUNT` and `GEE_PRIVATE_KEY_JSON` as secret environment values.
4. Ensure the service account is registered for Earth Engine and can use project `urbancool-mumbai-vk-2026`.
5. Deploy and check `/health` before sharing the submission URL.

For any public host, use a dedicated service account. Local browser authorization is not a production credential strategy.

## Core Formulas

NDVI:

```text
(NIR - RED) / (NIR + RED)
```

NDBI:

```text
(SWIR1 - NIR) / (SWIR1 + NIR)
```

Landsat LST:

```text
ST_B10 Kelvin = ST_B10 * 0.00341802 + 149.0
LST Celsius = Kelvin - 273.15
```

Heat Risk Score:

```text
HeatRisk = 0.50 * LST_norm + 0.30 * NDBI_norm + 0.20 * (1 - NDVI_norm)
```

Cooling priority:

```text
Priority = high LST + high NDBI + low NDVI
```

## Hackathon Story

Mumbai's pre-monsoon heat is intensified by dense built-up surfaces, low vegetation, and weak local ventilation. UrbanCool AI turns satellite and climate data into a decision dashboard for where to cool first and what type of cooling strategy is likely to work.

The MVP is intentionally label-free. Instead of depending on manual field labels or training polygons, it samples Earth Engine raster drivers directly and trains a lightweight Random Forest model to explain LST variation. This keeps the workflow fast, reproducible, and defensible for a hackathon.

The dashboard gives judges a clear path:

1. See present-day thermal stress.
2. Understand why the hotspots exist.
3. Compare intervention scenarios.
4. Export a concise action report.

## Limitations

- The model is an explanatory MVP, not a calibrated urban climate model.
- ERA5 is coarse compared with neighborhood-scale heat exposure.
- `ECMWF/ERA5/DAILY` ends on 2020-07-09 in Earth Engine. Later analysis periods use a clearly reported 2015-2019 same-season ERA5 climatology while Landsat remains period-specific.
- The cool roof scenario uses built-up intensity as an albedo proxy, not measured roof material.
- Water-body and blue-green corridor priority is heuristic.
- GEE map tile URLs are temporary and should be regenerated per analysis session.
- Cloud cover and Landsat revisit timing can affect the composite.

## Future Scope

- Add ward boundaries and population exposure once a permitted boundary dataset is available.
- Include Sentinel-2 for finer vegetation and built-up detail.
- Add uncertainty bands for cooling scenarios.
- Use temporal heatwave detection across multiple summers.
- Add equity layers such as vulnerable population and outdoor worker exposure.
- Export PDF reports and GeoJSON intervention zones.
- Deploy backend with a service account and scheduled cache refresh.

## Demo Tips

- Use the default date range `2024-03-01` to `2024-05-31` for a pre-monsoon heat narrative.
- Start the backend first, then the frontend.
- Run `/health` before presenting to confirm Earth Engine authentication.
- If the first `/analyze` call takes time, let it finish; later tile and report requests reuse the cached analysis context.
