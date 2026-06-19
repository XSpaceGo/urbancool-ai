import { CloudSun, Database, Satellite } from "lucide-react";

export default function ProvenanceBar({ provenance, period }) {
  return (
    <section className="provenance-bar" aria-label="Data provenance">
      <div><Satellite size={17} /><span>Thermal observation</span><strong>Landsat 8 + 9 L2</strong></div>
      <div><CloudSun size={17} /><span>Atmospheric context</span><strong>{provenance?.meteorology_period || "ERA5 Daily"}</strong></div>
      <div><Database size={17} /><span>Land cover</span><strong>ESA WorldCover 10 m</strong></div>
      <div className="analysis-period"><span>Analysis window</span><strong>{period ? `${period.start} / ${period.end}` : "Awaiting analysis"}</strong></div>
    </section>
  );
}
