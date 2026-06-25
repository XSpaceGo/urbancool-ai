const API_BASE = (
  import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "")
).replace(/\/$/, "");

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function healthCheck() {
  return request("/health");
}

export function getAreas() {
  return request("/areas");
}

export function runAnalysis(start = "2024-03-01", end = "2024-05-31", area = "mumbai") {
  return request(`/analyze?area=${encodeURIComponent(area)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
}

export function getTileLayer(layer) {
  return request(`/tiles/${layer}`);
}

export async function downloadReport() {
  const response = await fetch(`${API_BASE}/report`);
  if (!response.ok) {
    throw new Error("Report download failed");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "coolgrid-urban-decision-brief.md";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
