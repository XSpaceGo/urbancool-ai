import { useEffect, useState } from "react";
import { Activity, BarChart3, CalendarDays, Grid3X3, Map, MapPin, Play, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { downloadReport, getAreas, runAnalysis } from "./api";
import DriverChart from "./components/DriverChart";
import HotspotTable from "./components/HotspotTable";
import MapView from "./components/MapView";
import RecommendationPanel from "./components/RecommendationPanel";
import ScenarioPanel from "./components/ScenarioPanel";
import StatsCards from "./components/StatsCards";
import ProvenanceBar from "./components/ProvenanceBar";
import "./styles.css";

export default function App() {
  const [start, setStart] = useState("2024-03-01");
  const [end, setEnd] = useState("2024-05-31");
  const [area, setArea] = useState("mumbai");
  const [areas, setAreas] = useState([{ id: "mumbai", name: "Mumbai", state: "Maharashtra" }]);
  const [analysis, setAnalysis] = useState(null);
  const [activeLayer, setActiveLayer] = useState("heat_risk");
  const [loading, setLoading] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    setLoading(true);
    setError("");
    try {
      const data = await runAnalysis(start, end, area);
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleReport() {
    setLoadingReport(true);
    setError("");
    try {
      await downloadReport();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingReport(false);
    }
  }

  useEffect(() => {
    async function initialAnalyze() {
      setLoading(true);
      setError("");
      try {
        const [areaOptions, data] = await Promise.all([
          getAreas(),
          runAnalysis("2024-03-01", "2024-05-31", "mumbai"),
        ]);
        setAreas(areaOptions);
        setAnalysis(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    initialAnalyze();
  }, []);

  return (
    <div className="product-shell">
      <aside className="product-rail">
        <div className="brand-mark"><Grid3X3 size={23} /></div>
        <nav aria-label="Workspace sections">
          <a href="#command" title="Command center"><Map size={20} /></a>
          <a href="#evidence" title="Driver evidence"><BarChart3 size={20} /></a>
          <a href="#interventions" title="Interventions"><Sparkles size={20} /></a>
        </nav>
        <div className="rail-status" title="Earth Engine configured"><Activity size={18} /></div>
      </aside>

      <main className="app-shell">
        <header className="product-header">
          <div className="brand-copy">
            <div className="brand-lockup">
              <span>CoolGrid</span>
              <strong>Urban</strong>
            </div>
            <p>Urban heat decision intelligence</p>
          </div>
          <div className="system-status"><ShieldCheck size={16} /> Physics-informed AIML</div>
        </header>

        <section className="page-heading" id="command">
          <div>
            <p className="eyebrow">City-scale intervention planning</p>
            <h1>Heat Mitigation Command Center</h1>
            <p className="page-summary">Locate thermal stress, explain its drivers, and prioritize cooling investments for the selected urban area.</p>
          </div>
          <div className="date-controls">
            <label className="area-control" aria-label="Analysis area">
              <MapPin size={16} />
              <select value={area} onChange={(event) => setArea(event.target.value)}>
                {areas.map((option) => <option value={option.id} key={option.id}>{option.name}, {option.state}</option>)}
              </select>
            </label>
            <label aria-label="Start date">
              <CalendarDays size={16} />
              <input value={start} onChange={(event) => setStart(event.target.value)} type="date" />
            </label>
            <label aria-label="End date">
              <CalendarDays size={16} />
              <input value={end} onChange={(event) => setEnd(event.target.value)} type="date" />
            </label>
            <button type="button" onClick={analyze} disabled={loading}>
              {loading ? <RefreshCw size={18} className="spin" /> : <Play size={18} />}
              {loading ? "Computing" : "Run analysis"}
            </button>
          </div>
        </section>

        {error && <div className="error-banner">{error}</div>}

        <StatsCards stats={analysis?.stats} model={analysis?.model} />
        <ProvenanceBar provenance={analysis?.data_provenance} period={analysis?.period} />

        <section className="section-heading">
          <div><span>01</span><h2>Spatial Heat Intelligence</h2></div>
          <p>Observed conditions and decision surfaces</p>
        </section>

        <div className="dashboard-grid">
        <MapView
          tiles={analysis?.tiles}
          activeLayer={activeLayer}
          onLayerChange={setActiveLayer}
          zones={analysis?.top_zones}
          loading={loading}
          aoi={analysis?.aoi}
          areaName={analysis?.area?.name}
        />
        <aside className="side-column">
          <DriverChart
            groupedImportance={analysis?.grouped_importance}
            featureImportance={analysis?.feature_importance}
          />
        </aside>
        </div>

        <section className="section-heading" id="evidence">
          <div><span>02</span><h2>Model Evidence</h2></div>
          <p>Validated drivers and intervention response</p>
        </section>

        <div className="evidence-grid">
        <ScenarioPanel scenarios={analysis?.scenarios} optimalStrategy={analysis?.optimal_strategy} />
        <RecommendationPanel
          recommendations={analysis?.recommendations}
          model={analysis?.model}
          onDownload={handleReport}
          loadingReport={loadingReport}
        />
        </div>

        <section className="section-heading" id="interventions">
          <div><span>03</span><h2>Priority Action Register</h2></div>
          <p>Ranked spatial placement and expected cooling</p>
        </section>
        <HotspotTable zones={analysis?.top_zones} />

        <footer className="product-footer">
          <span>CoolGrid Urban</span>
          <p>Decision-support estimates derived from Landsat, ERA5 Daily, ESA WorldCover, and physics-informed machine learning.</p>
        </footer>
      </main>
    </div>
  );
}
