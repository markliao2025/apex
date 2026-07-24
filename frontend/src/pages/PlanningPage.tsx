/**
 * PlanningPage — Main satellite task planning interface
 *
 * Features:
 * - Natural language input for planning requests
 * - Intent parsing and summary display
 * - Schedule visualization with Gantt chart and map
 * - Task details and management
 * - Urgent re-planning modal
 */

import { useState, useCallback, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { planningApi, satelliteApi, tenancyApi } from "../lib/api";
import { ParsedIntent, PlanningRequest } from "../types";
import { GanttChart } from "../components/planning/GanttChart";
import { MapViewer } from "../components/planning/MapViewer";
import { IntentSummaryCard } from "../components/planning/IntentSummaryCard";
import { ReplanModal } from "../components/planning/ReplanModal";
import {
  Rocket,
  Loader2,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Download,
  Eye,
} from "lucide-react";

export default function PlanningPage() {
  const [rawInput, setRawInput] = useState("");
  const [selectedRequest, setSelectedRequest] = useState<string | null>(null);
  const [showReplanModal, setShowReplanModal] = useState(false);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"gantt" | "map">("gantt");
  const [constellationId, setConstellationId] = useState("");
  const queryClient = useQueryClient();

  // ── Parse mutation ────────────────────────────────────────────────────────────
  const parseMutation = useMutation({
    mutationFn: (text: string) => planningApi.parse(text, constellationId),
  });

  // ── Create request mutation ──────────────────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: (text: string) => planningApi.createRequest(text, constellationId),
    onSuccess: (data) => {
      setSelectedRequest(data.id || data.request_id);
      queryClient.invalidateQueries({ queryKey: ["requests"] });
    },
  });

  // ── Fetch scheduled request ─────────────────────────────────────────────────
  const { data: scheduledData, error: queryError } = useQuery<PlanningRequest>({
    queryKey: ["scheduled", selectedRequest],
    queryFn: () => planningApi.getRequest(selectedRequest!) as Promise<PlanningRequest>,
    enabled: !!selectedRequest,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === "planning" || data?.status === "pending" ? 3000 : false;
    },
  });

  const { data: constellations = [] } = useQuery({
    queryKey: ["constellations"],
    queryFn: () => tenancyApi.listConstellations(),
  });
  useEffect(() => {
    if (!constellationId && constellations.length > 0) {
      setConstellationId(constellations[0].id);
    }
  }, [constellationId, constellations]);

  // ── Fetch satellites ────────────────────────────────────────────────────────
  const { data: satellites = [] } = useQuery({
    queryKey: ["satellites", constellationId],
    queryFn: () => satelliteApi.list(constellationId),
    enabled: Boolean(constellationId),
  });

  // ── Fetch ground stations ───────────────────────────────────────────────────
  const { data: groundStations = [] } = useQuery({
    queryKey: ["groundStations"],
    queryFn: () => satelliteApi.listGroundStations(),
  });

  // ── Handle generate ─────────────────────────────────────────────────────────
  const handleGenerate = useCallback(() => {
    if (rawInput.length < 10) return;
    parseMutation.mutate(rawInput);
  }, [rawInput, parseMutation]);

  // ── Handle schedule ─────────────────────────────────────────────────────────
  const handleSchedule = useCallback(() => {
    if (rawInput.length < 10) return;
    createMutation.mutate(rawInput);
  }, [rawInput, createMutation]);

  // ── Handle task click ────────────────────────────────────────────────────────
  const handleTaskClick = useCallback((taskId: string) => {
    setExpandedTask(expandedTask === taskId ? null : taskId);
  }, [expandedTask]);

  // ── Handle replan success ───────────────────────────────────────────────────
  const handleReplanSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["scheduled", selectedRequest] });
  }, [queryClient, selectedRequest]);

  // ── Export schedule as JSON ──────────────────────────────────────────────────
  const handleExport = useCallback(() => {
    if (!scheduledData) return;
    const data = JSON.stringify(scheduledData.tasks, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `schedule-${scheduledData.id || "export"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [scheduledData]);

  return (
    <div className="space-y-6">
      {/* ── Input Card ────────────────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Rocket className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white">
            New Planning Request
          </h2>
        </div>

        <div className="relative">
          <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Planning constellation
          </label>
          <select
            value={constellationId}
            onChange={(event) => setConstellationId(event.target.value)}
            className="mb-4 w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-800 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
          >
            <option value="">Select a constellation</option>
            {constellations.map((constellation) => (
              <option key={constellation.id} value={constellation.id}>
                {constellation.name} · {constellation.satellite_count} satellites
              </option>
            ))}
          </select>
          <textarea
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            placeholder="Describe your planning request... e.g., &quot;Image Tokyo Bay next 3 days at resolution better than 3m for flood monitoring&quot;"
            className="w-full min-h-[100px] px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition resize-none"
          />
          <span className="absolute bottom-3 right-3 text-xs text-slate-400">
            {rawInput.length}/500
          </span>
        </div>

        <div className="flex gap-3 mt-4">
          <button
            onClick={handleGenerate}
            disabled={parseMutation.isPending || rawInput.length < 10 || !constellationId}
            className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-600/25"
          >
            {parseMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
            {parseMutation.isPending ? "Parsing..." : "Parse Intent"}
          </button>

          <button
            onClick={handleSchedule}
            disabled={createMutation.isPending || rawInput.length < 10 || !constellationId}
            className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-xl font-medium hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-green-600/25"
          >
            {createMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Zap className="w-5 h-5" />
            )}
            {createMutation.isPending ? "Scheduling..." : "Schedule Now"}
          </button>
        </div>

        {queryError && (
          <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            {queryError.message}
          </div>
        )}
      </div>

      {/* ── Intent Summary Card ───────────────────────────────────────────────── */}
      {parseMutation.data && (
        <IntentSummaryCard
          intent={parseMutation.data.parsed_intent as unknown as ParsedIntent}
          status={parseMutation.data.status}
          rawInput={rawInput}
          confidence={parseMutation.data.confidence}
        />
      )}

      {/* ── Schedule Viewer ───────────────────────────────────────────────────── */}
      {scheduledData && scheduledData.tasks && scheduledData.tasks.length > 0 && (
        <ScheduleViewer
          request={scheduledData}
          satellites={satellites}
          groundStations={groundStations}
          expandedTaskId={expandedTask}
          onTaskClick={handleTaskClick}
          onReplanClick={() => setShowReplanModal(true)}
          onExport={handleExport}
          activeView={activeView}
          onViewChange={setActiveView}
        />
      )}

      {/* ── Planning in progress ──────────────────────────────────────────────── */}
      {scheduledData && scheduledData.tasks?.length === 0 &&
       (scheduledData.status === "planning" || scheduledData.status === "pending") && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white">
              Scheduling in progress...
            </h3>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            Analyzing orbit windows, running CP-SAT solver, and validating tasks.
          </p>
        </div>
      )}

      {/* ── Recent Requests Placeholder ─────────────────────────────────────── */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-slate-500" />
          Recent Requests
        </h3>
        <div className="text-center py-8 text-slate-500 dark:text-slate-400">
          <p>Start by typing a planning request above</p>
        </div>
      </div>

      {/* ── Replan Modal ─────────────────────────────────────────────────────── */}
      <ReplanModal
        requestId={scheduledData?.id || selectedRequest || ""}
        isOpen={showReplanModal}
        onClose={() => setShowReplanModal(false)}
        currentTasks={scheduledData?.tasks || []}
        satellites={satellites.map((s: any) => ({ id: s.id, name: s.name }))}
        onReplanSuccess={handleReplanSuccess}
      />
    </div>
  );
}

// ── Schedule Viewer Component ─────────────────────────────────────────────────

interface ScheduleViewerProps {
  request: PlanningRequest;
  satellites: any[];
  groundStations: any[];
  expandedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  onReplanClick: () => void;
  onExport: () => void;
  activeView: "gantt" | "map";
  onViewChange: (view: "gantt" | "map") => void;
}

function ScheduleViewer({
  request,
  satellites,
  groundStations,
  expandedTaskId,
  onTaskClick,
  onReplanClick,
  onExport,
  activeView,
  onViewChange,
}: ScheduleViewerProps) {
  const satelliteMap = useMemo(
    () => new Map(satellites.map((s: any) => [s.id, s])),
    [satellites]
  );

  const stats = useMemo(() => {
    const tasks = request.tasks || [];
    const passed = tasks.filter((t: any) => t.validator_status === "passed").length;
    const failed = tasks.length - passed;
    const avgElevation = tasks.length > 0
      ? tasks.reduce((sum: number, t: any) => sum + (t.event_window?.max_elevation_deg || 0), 0) / tasks.length
      : 0;
    return { total: tasks.length, passed, failed, avgElevation };
  }, [request.tasks]);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white">
            Schedule
          </h3>
          <div className="flex items-center gap-2 text-sm">
            <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full">
              {stats.total} task{stats.total !== 1 ? "s" : ""}
            </span>
            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
              {stats.passed} passed
            </span>
            {stats.failed > 0 && (
              <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full">
                {stats.failed} failed
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* View Toggle */}
          <div className="flex bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
            <button
              onClick={() => onViewChange("gantt")}
              className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                activeView === "gantt"
                  ? "bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-500 dark:text-slate-400"
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => onViewChange("map")}
              className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                activeView === "map"
                  ? "bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-500 dark:text-slate-400"
              }`}
            >
              Map
            </button>
          </div>

          {/* Actions */}
          <button
            onClick={onReplanClick}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-lg hover:bg-orange-200 dark:hover:bg-orange-900/50 transition"
            title="Re-plan with different settings"
          >
            <RefreshCw className="w-4 h-4" />
            Re-plan
          </button>
          <button
            onClick={onExport}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition"
            title="Export as JSON"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 p-4">
        {/* Main View */}
        <div className="lg:col-span-3 min-h-[400px]">
          {activeView === "gantt" ? (
            <GanttChart
              tasks={request.tasks || []}
              satellites={satellites.map((s: any) => ({ id: s.id, name: s.name }))}
              selectedTaskId={expandedTaskId || undefined}
              onTaskClick={(task) => onTaskClick(task.id)}
            />
          ) : (
            <MapViewer
              tasks={request.tasks || []}
              groundStations={groundStations.map((gs: any) => ({
                id: gs.id,
                name: gs.name,
                latitude: gs.latitude,
                longitude: gs.longitude,
              }))}
              selectedTaskId={expandedTaskId || undefined}
              onTaskClick={(task) => onTaskClick(task.id)}
            />
          )}
        </div>

        {/* Task List */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-600 dark:text-slate-400 flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Tasks ({stats.total})
          </h4>

          {(request.tasks || []).map((task: any, idx: number) => (
            <TaskCard
              key={task.id}
              task={task}
              index={idx}
              isExpanded={expandedTaskId === task.id}
              onToggle={() => onTaskClick(task.id)}
              satellite={satelliteMap.get(task.satellite_id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Task Card Component ────────────────────────────────────────────────────────

function TaskCard({
  task,
  index,
  isExpanded,
  onToggle,
  satellite,
}: {
  task: any;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  satellite?: any;
}) {
  const isPassed = task.validator_status === "passed";
  const startTime = new Date(task.event_window?.aos_time);

  return (
    <div className="bg-white dark:bg-slate-700 rounded-xl border border-slate-200 dark:border-slate-600 overflow-hidden transition-all">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full text-left p-3 hover:bg-slate-50 dark:hover:bg-slate-600/50 transition"
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isPassed ? "bg-green-500" : "bg-yellow-500"
              }`}
            />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Task {index + 1}
            </span>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {isExpanded ? "▲" : "▼"}
          </span>
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {satellite?.name || task.satellite_id?.substring(0, 8) || "Unknown"}
        </div>
        <div className="flex gap-2 mt-2 text-xs text-slate-500 dark:text-slate-400">
          <span>{startTime.toLocaleDateString()}</span>
          <span>{startTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        </div>
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-3 pb-3 pt-0 space-y-2 border-t border-slate-100 dark:border-slate-600">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs pt-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Elevation</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {task.event_window?.max_elevation_deg?.toFixed(1) || "—"}°
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Duration</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {task.event_window?.los_time && task.event_window?.aos_time
                  ? `${Math.round((new Date(task.event_window.los_time).getTime() - new Date(task.event_window.aos_time).getTime()) / 1000)}s`
                  : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Battery</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">
                -{task.resource_allocation?.battery_delta_percent?.toFixed(1) || "0"}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Data</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {task.resource_allocation?.storage_mb?.toFixed(0) || "0"} MB
              </span>
            </div>
          </dl>

          {/* Status */}
          <div className={`mt-2 p-2 rounded-lg text-xs font-medium text-center ${
            isPassed
              ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
              : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400"
          }`}>
            {isPassed ? (
              <span className="flex items-center justify-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Validated
              </span>
            ) : (
              <span className="flex items-center justify-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Needs Review
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
