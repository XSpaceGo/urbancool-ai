import { BrainCircuit, Flame, Leaf, MapPinned, ThermometerSun, Wind } from "lucide-react";

const cards = [
  { key: "mean_lst", label: "Mean LST", suffix: "C", icon: ThermometerSun },
  { key: "p90_lst", label: "P90 LST", suffix: "C", icon: Flame },
  { key: "mean_ndvi", label: "Mean NDVI", suffix: "", icon: Leaf },
  { key: "estimated_avg_reduction", label: "Avg Cooling", suffix: "C", icon: Wind },
  { key: "hotspot_area_sq_km", label: "Hotspot Area", suffix: "km2", icon: MapPinned },
];

export default function StatsCards({ stats, model }) {
  const displayCards = [
    ...cards,
    { key: "model_r2", label: "Model R2", suffix: "", icon: BrainCircuit, value: model?.r2?.toFixed(2) },
  ];
  return (
    <section className="stats-grid" aria-label="Analysis statistics">
      {displayCards.map(({ key, label, suffix, icon: Icon, value }) => (
        <article className="stat-card" key={key}>
          <div className="stat-icon">
            <Icon size={20} />
          </div>
          <div>
            <p>{label}</p>
            <strong>
              {value ?? stats?.[key] ?? "--"}
              {suffix && <span> {suffix}</span>}
            </strong>
          </div>
        </article>
      ))}
    </section>
  );
}
