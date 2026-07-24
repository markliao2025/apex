import axios from "axios";
import {
  Constellation,
  ConstellationSatellite,
  DemoReplay,
  Organization,
  PlanningImpact,
  Satellite,
  TokenPair,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Auth interceptors ────────────────────────────────────────────────────────

function getAccessToken(): string | null {
  try {
    return localStorage.getItem("access_token") || null;
  } catch {
    return null;
  }
}

function getRefreshToken(): string | null {
  try {
    return localStorage.getItem("refresh_token") || null;
  } catch {
    return null;
  }
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

async function refreshToken(): Promise<string> {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("No refresh token");

  const response = await axios.post<TokenPair>(
    `${API_BASE}/api/v1/auth/refresh`,
    { refresh_token: refresh }
  );
  localStorage.setItem("access_token", response.data.access_token);
  localStorage.setItem("refresh_token", response.data.refresh_token);
  return response.data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshToken();
        onRefreshed(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch {
        // Clear auth state on refresh failure
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── Auth endpoints ───────────────────────────────────────────────────────────

export const authApi = {
  async register(email: string, password: string, name?: string) {
    const response = await api.post("/api/v1/auth/register", {
      email,
      password,
      name,
    });
    return response.data;
  },

  async login(email: string, password: string) {
    const response = await api.post<TokenPair>("/api/v1/auth/login", {
      email,
      password,
    });
    localStorage.setItem("access_token", response.data.access_token);
    localStorage.setItem("refresh_token", response.data.refresh_token);
    return response.data;
  },

  async getMe() {
    const response = await api.get("/api/v1/auth/me");
    return response.data;
  },

  async demoSession() {
    const response = await api.post<TokenPair>("/api/v1/demo/session");
    localStorage.setItem("access_token", response.data.access_token);
    localStorage.setItem("refresh_token", response.data.refresh_token);
    return response.data;
  },

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
};

// ── Planning endpoints ───────────────────────────────────────────────────────

export const planningApi = {
  async parse(raw_input: string, constellation_id?: string) {
    const response = await api.post("/api/v1/planning/parse", { raw_input, constellation_id });
    return response.data;
  },

  async createRequest(raw_input: string, constellation_id?: string) {
    const response = await api.post("/api/v1/planning/requests", { raw_input, constellation_id });
    return response.data;
  },

  async getRequest(id: string) {
    const response = await api.get(`/api/v1/planning/requests/${id}`);
    return response.data;
  },

  async cancelRequest(id: string) {
    const response = await api.post(`/api/v1/planning/requests/${id}/cancel`);
    return response.data;
  },

  async replanRequest(id: string, options: { priority_override?: string; time_horizon_hours?: number; satellite_id?: string }) {
    const response = await api.post(`/api/v1/planning/requests/${id}/replan`, options);
    return response.data;
  },

  async replan(id: string, options: {
    priority_override?: string;
    time_horizon_hours?: number;
    satellite_id?: string;
  }) {
    const response = await api.post(`/api/v1/planning/requests/${id}/replan`, options);
    return response.data;
  },

  async listRequests() {
    // Placeholder — would need a GET /planning/requests endpoint
    return [];
  },
};

// ── Satellite endpoints ──────────────────────────────────────────────────────

export const satelliteApi = {
  async list(constellation_id?: string) {
    const response = await api.get<Satellite[]>("/api/v1/satellites/", {
      params: { constellation_id },
    });
    return response.data;
  },

  async catalog() {
    const response = await api.get<Satellite[]>("/api/v1/satellites/catalog");
    return response.data;
  },

  async get(id: string) {
    const response = await api.get(`/api/v1/satellites/${id}`);
    return response.data;
  },

  async getOverpass(satelliteId: string, groundStationId: string, hours: number = 48) {
    const response = await api.get(
      `/api/v1/satellites/${satelliteId}/overpass`,
      { params: { ground_station_id: groundStationId, hours } }
    );
    return response.data;
  },

  async getGroundTrack(satelliteId: string, hours: number = 24) {
    const response = await api.get(
      `/api/v1/satellites/${satelliteId}/ground-track`,
      { params: { hours } }
    );
    return response.data;
  },

  async listGroundStations() {
    const response = await api.get("/api/v1/satellites/ground-stations/list");
    return response.data;
  },

  async getImagingWindows(params: {
    satellite_id: string;
    bbox: { sw_lat: number; sw_lng: number; ne_lat: number; ne_lng: number };
    hours: number;
  }) {
    const response = await api.post("/api/v1/orbit/imaging-windows", params);
    return response.data;
  },
};

export const tenancyApi = {
  async listOrganizations() {
    const response = await api.get<Organization[]>("/api/v1/organizations");
    return response.data;
  },

  async listConstellations(organization_id?: string) {
    const response = await api.get<Constellation[]>("/api/v1/constellations", {
      params: { organization_id },
    });
    return response.data;
  },

  async createConstellation(input: {
    organization_id: string;
    name: string;
    slug: string;
    description?: string;
  }) {
    const response = await api.post<Constellation>("/api/v1/constellations", input);
    return response.data;
  },

  async listSatellites(constellationId: string) {
    const response = await api.get<ConstellationSatellite[]>(
      `/api/v1/constellations/${constellationId}/satellites`,
    );
    return response.data;
  },

  async attachSatellite(constellationId: string, satellite_id: string) {
    const response = await api.post<ConstellationSatellite>(
      `/api/v1/constellations/${constellationId}/satellites`,
      { satellite_id },
    );
    return response.data;
  },

  async detachSatellite(constellationId: string, satelliteId: string) {
    await api.delete(
      `/api/v1/constellations/${constellationId}/satellites/${satelliteId}`,
    );
  },
};

export const demoApi = {
  async createReplay() {
    const response = await api.post<DemoReplay>("/api/v1/demo/replays", {
      fixture_id: "apex-synthetic-001",
    });
    return response.data;
  },

  async planningImpact(
    replayId: string,
    input: {
      constellation_id: string;
      satellite_id: string;
      unavailable_from_utc: string;
      unavailable_to_utc: string;
      reason: "synthetic_conjunction_what_if";
    },
  ) {
    const response = await api.post<PlanningImpact>(
      `/api/v1/demo/replays/${replayId}/planning-impact`,
      input,
    );
    return response.data;
  },

  async exportReplay(replayId: string, format: "json" | "md") {
    const response = await api.get(
      `/api/v1/demo/replays/${replayId}/export`,
      { params: { format }, responseType: "blob" },
    );
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `apex-synthetic-001-evidence.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  },
};

// ── Export default ────────────────────────────────────────────────────────────

export default api;
