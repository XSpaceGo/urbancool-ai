import { Layers, LoaderCircle, MapPin } from "lucide-react";
import { MapContainer, TileLayer, Rectangle, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const bounds = [
  [18.85, 72.75],
  [19.3, 73.05],
];

const layerOptions = [
  { key: "lst", label: "Heat Hotspot LST" },
  { key: "heat_risk", label: "Heat Risk" },
  { key: "priority", label: "Cooling Priority" },
  { key: "cooling_reduction", label: "Temp Reduction" },
  { key: "ndvi", label: "NDVI" },
  { key: "ndbi", label: "NDBI" },
  { key: "greening_reduction", label: "Greening" },
  { key: "cool_roof_reduction", label: "Cool Roof" },
  { key: "blue_green_reduction", label: "Blue-Green" },
];

const hotspotIcon = L.divIcon({
  className: "hotspot-marker",
  html: '<span></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const legends = {
  lst: ["25 C", "Surface temperature", "48 C"],
  heat_risk: ["Low", "Heat risk", "Critical"],
  priority: ["Monitor", "Cooling priority", "Act now"],
  cooling_reduction: ["0 C", "Cooling potential", "5 C"],
  ndvi: ["Sparse", "Vegetation", "Dense"],
  ndbi: ["Low", "Built-up signal", "High"],
  greening_reduction: ["0 C", "Greening effect", "3 C"],
  cool_roof_reduction: ["0 C", "Cool-roof effect", "1.5 C"],
  blue_green_reduction: ["0 C", "Blue-green effect", "1.75 C"],
};

export default function MapView({ tiles, activeLayer, onLayerChange, zones, loading }) {
  const tileUrl = tiles?.[activeLayer];

  return (
    <section className="map-section">
      <div className="map-toolbar" aria-label="Map layers">
        <div className="toolbar-title">
          <Layers size={18} />
          Layers
        </div>
        <div className="layer-switcher">
          {layerOptions.map((layer) => (
            <button
              className={activeLayer === layer.key ? "active" : ""}
              key={layer.key}
              type="button"
              onClick={() => onLayerChange(layer.key)}
            >
              {layer.label}
            </button>
          ))}
        </div>
      </div>

      <MapContainer bounds={bounds} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {tileUrl && <TileLayer key={activeLayer} url={tileUrl} opacity={0.74} />}
        <Rectangle bounds={bounds} pathOptions={{ color: "#111827", weight: 2, fill: false }} />
        {zones?.slice(0, 10).map((zone) => (
          <Marker key={`${zone.rank}-${zone.lat}-${zone.lon}`} position={[zone.lat, zone.lon]} icon={hotspotIcon}>
            <Popup>
              <strong>#{zone.rank} {zone.zone}</strong>
              <br />
              Priority: {zone.priority}
              <br />
              LST: {zone.lst} C
              <br />
              {zone.recommendation}
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {loading && (
        <div className="map-loading"><LoaderCircle className="spin" size={24} /><strong>Computing city model</strong><span>Satellite compositing, sampling and optimization</span></div>
      )}

      <div className={`map-legend legend-${activeLayer}`}>
        <span>{legends[activeLayer]?.[0]}</span>
        <div />
        <strong>{legends[activeLayer]?.[1]}</strong>
        <span>{legends[activeLayer]?.[2]}</span>
      </div>

      <div className="map-footnote">
        <MapPin size={16} />
        Mumbai AOI: 72.75, 18.85, 73.05, 19.30
      </div>
    </section>
  );
}
