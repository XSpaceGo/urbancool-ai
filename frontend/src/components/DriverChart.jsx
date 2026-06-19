import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function DriverChart({ groupedImportance, featureImportance }) {
  const groupedData = Object.entries(groupedImportance || {}).map(([name, value]) => ({
    name: name.replace("_", " "),
    value: Math.round(value * 100),
  }));

  const featureData = Object.entries(featureImportance || {}).map(([name, value]) => ({
    name,
    value: Math.round(value * 100),
  }));

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>Urban Heating Drivers</h2>
        <span>Random Forest attribution</span>
      </div>
      <div className="chart-block">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={groupedData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis unit="%" tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="importance-list">
        {featureData.map((item) => (
          <div key={item.name}>
            <span>{item.name}</span>
            <meter min="0" max="100" value={item.value} />
            <strong>{item.value}%</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
