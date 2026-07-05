import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Button, Field, TextInput } from "./ui";

export interface LatLng {
  lat: number;
  lng: number;
}

// Uses circleMarker/circle (vector, no image assets) so it renders offline and
// needs no Leaflet marker-icon asset wiring under Vite.
export function MapPicker({
  value,
  onChange,
  radiusM,
}: {
  value: LatLng | null;
  onChange: (v: LatLng) => void;
  radiusM: number | null;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.CircleMarker | null>(null);
  const circleRef = useRef<L.Circle | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [query, setQuery] = useState("");
  const [geoError, setGeoError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, { center: [48.8566, 2.3522], zoom: 5 });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);
    map.on("click", (e: L.LeafletMouseEvent) => {
      onChangeRef.current({ lat: e.latlng.lat, lng: e.latlng.lng });
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Reflect the selected point + geofence circle onto the map.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !value) return;
    const latlng: L.LatLngExpression = [value.lat, value.lng];
    if (markerRef.current) {
      markerRef.current.setLatLng(latlng);
    } else {
      markerRef.current = L.circleMarker(latlng, {
        radius: 8,
        color: "#4f46e5",
        fillColor: "#4f46e5",
        fillOpacity: 0.9,
      }).addTo(map);
    }
    if (radiusM && radiusM > 0) {
      if (circleRef.current) {
        circleRef.current.setLatLng(latlng).setRadius(radiusM);
      } else {
        circleRef.current = L.circle(latlng, {
          radius: radiusM,
          color: "#6366f1",
          fillOpacity: 0.1,
        }).addTo(map);
      }
    } else if (circleRef.current) {
      circleRef.current.remove();
      circleRef.current = null;
    }
    map.panTo(latlng);
  }, [value, radiusM]);

  async function geocode() {
    if (!query.trim()) return;
    setSearching(true);
    setGeoError(null);
    try {
      const url = new URL("https://nominatim.openstreetmap.org/search");
      url.searchParams.set("format", "jsonv2");
      url.searchParams.set("q", query);
      url.searchParams.set("limit", "1");
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      const hits = (await res.json()) as Array<{ lat: string; lon: string }>;
      const first = hits[0];
      if (!first) {
        setGeoError("No match found — click the map to place the pin manually.");
        return;
      }
      const picked = { lat: Number(first.lat), lng: Number(first.lon) };
      onChangeRef.current(picked);
      mapRef.current?.setView([picked.lat, picked.lng], 14);
    } catch {
      setGeoError("Address lookup unavailable — click the map to place the pin.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <Field label="Search address">
            {({ id }) => (
              <TextInput
                id={id}
                value={query}
                placeholder="e.g. Paris Expo Porte de Versailles"
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void geocode();
                  }
                }}
              />
            )}
          </Field>
        </div>
        <Button type="button" variant="secondary" onClick={() => void geocode()} disabled={searching}>
          {searching ? "Searching…" : "Find"}
        </Button>
      </div>
      {geoError && <p className="text-sm text-amber-700">{geoError}</p>}
      <div
        ref={containerRef}
        role="application"
        aria-label="Map — click to place the event location"
        className="h-72 w-full overflow-hidden rounded-lg border border-slate-300"
      />
      {value && (
        <p className="text-xs text-slate-500">
          Pin at {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
        </p>
      )}
    </div>
  );
}
