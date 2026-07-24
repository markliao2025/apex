/**
 * MapViewer Component — Satellite Ground Track and Target Visualization
 *
 * Features:
 * - Target bounding box polygon
 * - Satellite ground track polylines
 * - Ground station markers
 * - Task location markers
 * - Legend and layer controls
 * - Supports multiple tile providers (OSM, satellite)
 */

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Layers, Satellite, MapPin, Radio, Eye, EyeOff } from "lucide-react";

interface MapTask {
  id: string;
  satellite_id: string;
  satellite_name?: string | null;
  target_location?: {
    latitude: number;
    longitude: number;
  };
  event_window: {
    aos_time: string;
    los_time: string;
    max_elevation_deg: number;
  };
  validator_status: string;
}

interface GroundStation {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
}

interface GroundTrack {
  satellite_id: string;
  points: { lat: number; lon: number; time: string }[];
  color: string;
}

interface MapViewerProps {
  tasks: MapTask[];
  groundStations: GroundStation[];
  groundTracks?: GroundTrack[];
  /** Target bounding box */
  targetBbox?: {
    sw_lat: number;
    sw_lng: number;
    ne_lat: number;
    ne_lng: number;
  };
  /** Initial center coordinates */
  center?: [number, number];
  /** Initial zoom level */
  zoom?: number;
  /** Tile provider: 'osm' | 'satellite' */
  tileProvider?: "osm" | "satellite";
  /** Callback when task is clicked */
  onTaskClick?: (task: MapTask) => void;
  /** Selected task ID */
  selectedTaskId?: string;
}

interface LayerVisibility {
  target: boolean;
  groundTrack: boolean;
  groundStations: boolean;
  taskMarkers: boolean;
}

export function MapViewer({
  tasks,
  groundStations,
  groundTracks = [],
  targetBbox,
  center = [35.6762, 139.6503], // Tokyo as default
  zoom = 4,
  tileProvider = "osm",
  onTaskClick,
  selectedTaskId,
}: MapViewerProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<Map<string, any>>(new Map());
  const polylinesRef = useRef<any[]>([]);
  const polygonsRef = useRef<any[]>([]);

  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    target: true,
    groundTrack: true,
    groundStations: true,
    taskMarkers: true,
  });

  // Satellite colors for ground tracks
  const SATELLITE_COLORS = [
    "#3B82F6", // blue
    "#22C55E", // green
    "#F97316", // orange
    "#A855F7", // purple
    "#EC4899", // pink
    "#06B6D4", // cyan
    "#8B5CF6", // indigo
    "#14B8A6", // teal
  ];

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const initMap = async () => {
      try {
        // Dynamically import Leaflet to avoid SSR issues
        const L = await import("leaflet");
        await import("leaflet/dist/leaflet.css");

        // Fix Leaflet default marker icons
        delete (L.Icon.Default.prototype as any)._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
          iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
          shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
        });

        // Create map
        const map = L.map(mapRef.current!, {
          center: center,
          zoom: zoom,
          scrollWheelZoom: true,
          doubleClickZoom: true,
          boxZoom: true,
          keyboard: true,
        });

        // Add tile layer
        addTileLayer(map, tileProvider, L);

        // Store reference
        mapInstanceRef.current = map;
        setIsLoaded(true);

        // Cleanup
        return () => {
          map.remove();
          mapInstanceRef.current = null;
        };
      } catch (err) {
        console.error("Failed to initialize map:", err);
        setError("Failed to load map. Please refresh the page.");
      }
    };

    initMap();
    // The map is intentionally constructed exactly once. Later provider changes
    // are handled by the dedicated effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Change tile layer when provider changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      // Remove existing tile layers
      mapInstanceRef.current.eachLayer((layer: any) => {
        if (layer instanceof L.TileLayer) {
          mapInstanceRef.current.removeLayer(layer);
        }
      });

      // Add new tile layer
      addTileLayer(mapInstanceRef.current, tileProvider, L);
    });
  }, [tileProvider]);

  // Add/Update layers
  useEffect(() => {
    if (!isLoaded || !mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      // Clear existing layers
      clearLayers();

      // Add target bounding box
      if (targetBbox && layerVisibility.target) {
        addTargetPolygon(targetBbox, L);
      }

      // Add ground tracks
      if (layerVisibility.groundTrack) {
        groundTracks.forEach((track, idx) => {
          addGroundTrack(track, SATELLITE_COLORS[idx % SATELLITE_COLORS.length], L);
        });
      }

      // Add ground stations
      if (layerVisibility.groundStations) {
        groundStations.forEach((station) => {
          addGroundStation(station, L);
        });
      }

      // Add task markers
      if (layerVisibility.taskMarkers) {
        tasks.forEach((task, idx) => {
          if (task.target_location) {
            addTaskMarker(task, SATELLITE_COLORS[idx % SATELLITE_COLORS.length], L);
          }
        });
      }

      // Fit bounds if we have content
      fitBounds(L);
    });
    // Leaflet layer helpers close over refs only; adding them would recreate all
    // layers on every render without changing the rendered map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, tasks, groundStations, groundTracks, targetBbox, layerVisibility]);

  // Helper functions
  const addTileLayer = (_map: any, provider: string, L: any) => {
    const tileUrls: Record<string, string> = {
      osm: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    };

    const attribution = provider === "osm"
      ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      : "Tiles &copy; Esri";

    L.tileLayer(tileUrls[provider], {
      attribution,
      maxZoom: 19,
    }).addTo(_map);
  };

  const clearLayers = () => {
    // Clear markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();

    // Clear polylines
    polylinesRef.current.forEach((polyline) => polyline.remove());
    polylinesRef.current = [];

    // Clear polygons
    polygonsRef.current.forEach((polygon) => polygon.remove());
    polygonsRef.current = [];
  };

  const addTargetPolygon = (bbox: typeof targetBbox, L: any) => {
    if (!bbox || !mapInstanceRef.current) return;

    const polygon = L.rectangle(
      [
        [bbox.sw_lat, bbox.sw_lng],
        [bbox.ne_lat, bbox.ne_lng],
      ],
      {
        color: "#3B82F6",
        fillColor: "#3B82F6",
        fillOpacity: 0.2,
        weight: 2,
        dashArray: "5, 5",
      }
    )
      .bindPopup("Target Area")
      .addTo(mapInstanceRef.current);

    polygonsRef.current.push(polygon);
  };

  const addGroundTrack = (track: GroundTrack, color: string, L: any) => {
    if (!mapInstanceRef.current || track.points.length < 2) return;

    const latlngs = track.points.map((p) => [p.lat, p.lon] as [number, number]);

    const polyline = L.polyline(latlngs, {
      color: color,
      weight: 2,
      opacity: 0.7,
      dashArray: "10, 5",
    })
      .bindPopup(`Ground Track: ${track.satellite_id}`)
      .addTo(mapInstanceRef.current);

    polylinesRef.current.push(polyline);
  };

  const addGroundStation = (station: GroundStation, L: any) => {
    if (!mapInstanceRef.current) return;

    const icon = L.divIcon({
      className: "ground-station-marker",
      html: `
        <div class="relative">
          <div class="w-6 h-6 bg-slate-700 rounded-full border-2 border-white shadow-lg flex items-center justify-center">
            <span class="text-white text-xs">📡</span>
          </div>
          <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-700"></div>
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 24],
    });

    const marker = L.marker([station.latitude, station.longitude], { icon })
      .bindPopup(`
        <div class="text-sm">
          <strong>${station.name}</strong><br/>
          ${station.latitude.toFixed(4)}, ${station.longitude.toFixed(4)}
        </div>
      `)
      .addTo(mapInstanceRef.current);

    markersRef.current.set(`station-${station.id}`, marker);
  };

  const addTaskMarker = (task: MapTask, _color: string, L: any) => {
    if (!mapInstanceRef.current || !task.target_location) return;

    const isPassed = task.validator_status === "passed";
    const isSelected = task.id === selectedTaskId;

    const icon = L.divIcon({
      className: "task-marker",
      html: `
        <div class="
          w-8 h-8 rounded-full border-2 shadow-lg flex items-center justify-center
          ${isSelected ? "ring-4 ring-blue-500" : ""}
          ${isPassed ? "bg-green-500 border-green-300" : "bg-yellow-500 border-yellow-300"}
        ">
          <span class="text-white text-sm">${isPassed ? "✓" : "⚠"}</span>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const marker = L.marker(
      [task.target_location.latitude, task.target_location.longitude],
      { icon }
    )
      .bindPopup(`
        <div class="text-sm">
          <strong>Task: ${task.satellite_name || task.satellite_id}</strong><br/>
          Time: ${new Date(task.event_window.aos_time).toLocaleString()}<br/>
          Elevation: ${task.event_window.max_elevation_deg.toFixed(1)}°<br/>
          Status: ${task.validator_status}
        </div>
      `)
      .on("click", () => {
        onTaskClick?.(task);
      })
      .addTo(mapInstanceRef.current);

    markersRef.current.set(`task-${task.id}`, marker);
  };

  const fitBounds = (L: any) => {
    if (!mapInstanceRef.current) return;

    const bounds = L.latLngBounds([]);

    // Add target bbox
    if (targetBbox) {
      bounds.extend([targetBbox.sw_lat, targetBbox.sw_lng]);
      bounds.extend([targetBbox.ne_lat, targetBbox.ne_lng]);
    }

    // Add ground tracks
    groundTracks.forEach((track) => {
      track.points.forEach((p) => bounds.extend([p.lat, p.lon]));
    });

    // Add ground stations
    groundStations.forEach((station) => {
      bounds.extend([station.latitude, station.longitude]);
    });

    // Add task locations
    tasks.forEach((task) => {
      if (task.target_location) {
        bounds.extend([task.target_location.latitude, task.target_location.longitude]);
      }
    });

    // Only fit if we have valid bounds
    if (bounds.isValid()) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 });
    }
  };

  const toggleLayer = (layer: keyof LayerVisibility) => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layer]: !prev[layer],
    }));
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-100 dark:bg-slate-700 rounded-xl">
        <div className="text-center text-red-600 dark:text-red-400">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="map-viewer-container">
      {/* Map Container */}
      <div className="relative rounded-xl overflow-hidden">
        <div ref={mapRef} className="h-96 w-full" />

        {/* Loading Overlay */}
        {!isLoaded && (
          <div className="absolute inset-0 bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
            <div className="text-slate-500 dark:text-slate-400">Loading map...</div>
          </div>
        )}

        {/* Layer Controls */}
        <div className="absolute top-3 right-3 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-2 z-[1000]">
          <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 mb-2">
            <Layers className="w-3 h-3" />
            Layers
          </div>
          <div className="space-y-1">
            <LayerToggle
              icon={<Eye className="w-3 h-3" />}
              label="Target"
              active={layerVisibility.target}
              onClick={() => toggleLayer("target")}
            />
            <LayerToggle
              icon={<Satellite className="w-3 h-3" />}
              label="Ground Track"
              active={layerVisibility.groundTrack}
              onClick={() => toggleLayer("groundTrack")}
            />
            <LayerToggle
              icon={<Radio className="w-3 h-3" />}
              label="Stations"
              active={layerVisibility.groundStations}
              onClick={() => toggleLayer("groundStations")}
            />
            <LayerToggle
              icon={<MapPin className="w-3 h-3" />}
              label="Tasks"
              active={layerVisibility.taskMarkers}
              onClick={() => toggleLayer("taskMarkers")}
            />
          </div>
        </div>

        {/* Tile Provider Toggle */}
        <div className="absolute top-3 left-3 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-2 z-[1000]">
          <div className="flex gap-1">
            <button
              onClick={() => {}}
              className={`px-2 py-1 text-xs rounded ${
                tileProvider === "osm"
                  ? "bg-blue-500 text-white"
                  : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400"
              }`}
              title="OpenStreetMap"
            >
              OSM
            </button>
            <button
              onClick={() => {}}
              className={`px-2 py-1 text-xs rounded ${
                tileProvider === "satellite"
                  ? "bg-blue-500 text-white"
                  : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400"
              }`}
              title="Satellite Imagery"
            >
              Sat
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-3 text-xs">
        <LegendItem color="#3B82F6" label="Target Area" dashed />
        {groundTracks.slice(0, 3).map((track, idx) => (
          <LegendItem
            key={track.satellite_id}
            color={SATELLITE_COLORS[idx % SATELLITE_COLORS.length]}
            label={track.satellite_id.substring(0, 8)}
          />
        ))}
        <LegendItem color="#64748B" label="Ground Station" marker="📡" />
        <LegendItem color="#22C55E" label="Task (Passed)" marker="✓" />
        <LegendItem color="#EAB308" label="Task (Warning)" marker="⚠" />
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-500 dark:text-slate-400">
        {tasks.length} task{tasks.length !== 1 ? "s" : ""} • {groundStations.length} ground station{groundStations.length !== 1 ? "s" : ""} • {groundTracks.length} track{groundTracks.length !== 1 ? "s" : ""}
      </div>
    </div>
  );
}

// Layer Toggle Button
function LayerToggle({
  icon,
  label,
  active,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-2 px-2 py-1 rounded text-left
        ${active ? "text-slate-800 dark:text-slate-200" : "text-slate-400"}
      `}
    >
      {icon}
      <span className="flex-1">{label}</span>
      {active ? (
        <Eye className="w-3 h-3" />
      ) : (
        <EyeOff className="w-3 h-3" />
      )}
    </button>
  );
}

// Legend Item
function LegendItem({
  color,
  label,
  dashed,
  marker,
}: {
  color: string;
  label: string;
  dashed?: boolean;
  marker?: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      {marker ? (
        <span className="text-sm">{marker}</span>
      ) : (
        <span
          className={`w-4 h-0.5 ${dashed ? "border-t-2 border-dashed" : ""}`}
          style={{
            backgroundColor: dashed ? undefined : color,
            borderColor: color,
          }}
        />
      )}
      <span className="text-slate-600 dark:text-slate-400">{label}</span>
    </div>
  );
}

export default MapViewer;
