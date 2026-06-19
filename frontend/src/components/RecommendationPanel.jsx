import { Download, Sparkles } from "lucide-react";

export default function RecommendationPanel({ recommendations, model, onDownload, loadingReport }) {
  return (
    <section className="panel recommendation-panel">
      <div className="panel-heading">
        <h2>Decision Brief</h2>
        <span>{model?.rows_used || 0} GEE samples</span>
      </div>
      <div className="model-strip">
        <div>
          <p>Validation R2</p>
          <strong>{model?.r2 == null ? "N/A" : model.r2.toFixed(2)}</strong>
        </div>
        <div>
          <p>Validation MAE</p>
          <strong>{model?.mae == null ? "N/A" : `${model.mae.toFixed(2)} C`}</strong>
        </div>
        <div>
          <p>Validation RMSE</p>
          <strong>{model?.rmse == null ? "N/A" : `${model.rmse.toFixed(2)} C`}</strong>
        </div>
      </div>
      <ul className="recommendations">
        {(recommendations || []).map((item) => (
          <li key={item}>
            <Sparkles size={16} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
      <button className="download-button" type="button" onClick={onDownload} disabled={loadingReport}>
        <Download size={18} />
        {loadingReport ? "Preparing brief" : "Export decision brief"}
      </button>
    </section>
  );
}
