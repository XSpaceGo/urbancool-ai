import { Droplets, Layers3, Leaf, SunMedium } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const icons = {
  greening: Leaf,
  cool_roof: SunMedium,
  blue_green: Droplets,
  combined: Layers3,
};

export default function ScenarioPanel({ scenarios, optimalStrategy }) {
  const data = (scenarios || []).map((scenario) => ({
    ...scenario,
    shortLabel: scenario.label.replace(" portfolio", ""),
  }));

  return (
    <section className="panel scenario-panel">
      <div className="panel-heading">
        <h2>Scenario Optimizer</h2>
        <span>Physics + ML estimates</span>
      </div>
      <div className="scenario-chart">
        <ResponsiveContainer width="100%" height={210}>
          <BarChart data={data} layout="vertical" margin={{ left: 14 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" unit=" C" tickLine={false} axisLine={false} />
            <YAxis dataKey="shortLabel" type="category" width={112} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => `${value} C`} />
            <Bar dataKey="mean_reduction_c" fill="#d94830" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="scenario-grid">
        {data.map((scenario) => {
          const Icon = icons[scenario.key] || Layers3;
          return (
            <div className={scenario.key === optimalStrategy?.key ? "scenario-item optimal" : "scenario-item"} key={scenario.key}>
              <Icon size={18} />
              <div>
                <span>{scenario.label}</span>
                <strong>{scenario.mean_reduction_c} C</strong>
              </div>
            </div>
          );
        })}
      </div>
      {optimalStrategy && (
        <div className="optimal-callout">
          <span>Optimized strategy</span>
          <strong>{optimalStrategy.label}</strong>
          <p>{optimalStrategy.reason}</p>
        </div>
      )}
    </section>
  );
}
