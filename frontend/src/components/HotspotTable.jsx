export default function HotspotTable({ zones }) {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <h2>Intervention Deployment Matrix</h2>
        <span>Top 10 ranked 1 km cells</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Location</th>
              <th>LST</th>
              <th>NDVI</th>
              <th>Priority</th>
              <th>Reduction</th>
              <th>Recommended intervention</th>
            </tr>
          </thead>
          <tbody>
            {(zones || []).map((zone) => (
              <tr key={zone.rank}>
                <td>#{zone.rank}</td>
                <td>{zone.lat}, {zone.lon}</td>
                <td>{zone.lst} C</td>
                <td>{zone.ndvi}</td>
                <td>{zone.priority}</td>
                <td>{zone.estimated_reduction} C</td>
                <td>{zone.recommendation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
