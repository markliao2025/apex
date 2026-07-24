/**
 * ReplanModal Component — Urgent Re-planning Interface
 *
 * Features:
 * - Priority override selection
 * - Satellite swap options
 * - Time horizon adjustment
 * - Plan comparison (diff view)
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { planningApi } from "../../lib/api";
import { X, Zap, Clock, Satellite, RefreshCw, Loader2, Check } from "lucide-react";

interface ReplanModalProps {
  requestId: string;
  isOpen: boolean;
  onClose: () => void;
  currentTasks: any[];
  satellites: { id: string; name: string }[];
  onReplanSuccess?: () => void;
}

const PRIORITY_OPTIONS = [
  { value: "normal", label: "Normal", description: "Standard priority scheduling" },
  { value: "high", label: "High", description: "Prioritize urgent tasks over others" },
  { value: "urgent", label: "Urgent", description: "Emergency re-planning for critical events" },
];

const TIME_HORIZON_OPTIONS = [
  { value: 24, label: "24 hours" },
  { value: 48, label: "48 hours" },
  { value: 72, label: "3 days" },
  { value: 168, label: "7 days" },
];

export function ReplanModal({
  requestId,
  isOpen,
  onClose,
  currentTasks,
  satellites,
  onReplanSuccess,
}: ReplanModalProps) {
  const [priority, setPriority] = useState("high");
  const [timeHorizonHours, setTimeHorizonHours] = useState(48);
  const [satelliteSwap, setSatelliteSwap] = useState("");
  const [showDiff, setShowDiff] = useState(false);
  const [replanResult, setReplanResult] = useState<any>(null);

  const replanMutation = useMutation({
    mutationFn: () =>
      planningApi.replan(requestId, {
        priority_override: priority,
        satellite_id: satelliteSwap || undefined,
        time_horizon_hours: timeHorizonHours,
      }),
    onSuccess: (data) => {
      setReplanResult(data);
      setShowDiff(true);
      onReplanSuccess?.();
    },
  });

  const handleClose = () => {
    setShowDiff(false);
    setReplanResult(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <Zap className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800 dark:text-white">
                Re-plan Schedule
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Adjust parameters and re-optimize
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-5">
          {!showDiff ? (
            <>
              {/* Priority Override */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Priority Override
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {PRIORITY_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setPriority(option.value)}
                      className={`
                        p-3 rounded-xl border-2 text-left transition-all
                        ${priority === option.value
                          ? option.value === "urgent"
                            ? "border-red-500 bg-red-50 dark:bg-red-900/20"
                            : option.value === "high"
                            ? "border-orange-500 bg-orange-50 dark:bg-orange-900/20"
                            : "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                          : "border-slate-200 dark:border-slate-600 hover:border-slate-300"
                        }
                      `}
                    >
                      <div className={`
                        text-sm font-medium
                        ${priority === option.value
                          ? option.value === "urgent"
                            ? "text-red-700 dark:text-red-400"
                            : option.value === "high"
                            ? "text-orange-700 dark:text-orange-400"
                            : "text-blue-700 dark:text-blue-400"
                          : "text-slate-700 dark:text-slate-300"
                        }
                      `}>
                        {option.label}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {option.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Time Horizon */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Planning Time Horizon
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {TIME_HORIZON_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setTimeHorizonHours(option.value)}
                      className={`
                        py-2 px-3 rounded-lg border-2 text-sm font-medium transition-all
                        ${timeHorizonHours === option.value
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                          : "border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                        }
                      `}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Satellite Selection */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <Satellite className="w-4 h-4 inline mr-1" />
                  Available Satellites
                </label>
                <div className="max-h-32 overflow-y-auto border border-slate-200 dark:border-slate-600 rounded-lg divide-y divide-slate-200 dark:divide-slate-700">
                  {satellites.map((sat) => (
                    <label
                      key={sat.id}
                      className="flex items-center gap-3 p-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="preferred-satellite"
                        checked={satelliteSwap === sat.id}
                        onChange={(e) => {
                          setSatelliteSwap(e.target.checked ? sat.id : "");
                        }}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-slate-700 dark:text-slate-300">
                        {sat.name}
                      </span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Optionally prefer one satellite (leave empty for all available)
                </p>
              </div>
            </>
          ) : (
            /* Diff View */
            <DiffView
              oldTasks={currentTasks}
              newTasks={replanResult?.tasks || []}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
          {!showDiff ? (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => replanMutation.mutate()}
                disabled={replanMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition disabled:opacity-50"
              >
                {replanMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Re-planning...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Re-plan Now
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setShowDiff(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition"
              >
                Back to Settings
              </button>
              <button
                onClick={handleClose}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
              >
                <Check className="w-4 h-4" />
                Accept New Plan
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Diff View Component
function DiffView({
  oldTasks,
  newTasks,
}: {
  oldTasks: any[];
  newTasks: any[];
}) {
  const oldBySatellite = new Map(
    oldTasks.map((t) => [t.satellite_id, t])
  );

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
        <RefreshCw className="w-4 h-4" />
        Schedule Changes
      </h4>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Tasks Before"
          value={oldTasks.length}
          color="slate"
        />
        <StatCard
          label="Tasks After"
          value={newTasks.length}
          color={newTasks.length >= oldTasks.length ? "green" : "orange"}
        />
      </div>

      {/* Task Changes */}
      <div className="max-h-64 overflow-y-auto space-y-2">
        {newTasks.map((task: any, idx: number) => {
          const oldTask = oldBySatellite.get(task.satellite_id);
          const hasChanged = !oldTask ||
            new Date(task.event_window.aos_time).getTime() !==
            new Date(oldTask.event_window.aos_time).getTime();

          return (
            <div
              key={task.id}
              className={`
                p-3 rounded-lg border text-xs
                ${hasChanged
                  ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                  : "bg-slate-50 dark:bg-slate-700/50 border-slate-200 dark:border-slate-600"
                }
              `}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Task {idx + 1}
                </span>
                {hasChanged && (
                  <span className="text-blue-600 dark:text-blue-400 font-medium">
                    Modified
                  </span>
                )}
              </div>
              <div className="space-y-0.5 text-slate-600 dark:text-slate-400">
                <div>Satellite: {task.satellite_id?.substring(0, 8)}...</div>
                <div>
                  Time: {new Date(task.event_window.aos_time).toLocaleString()}
                </div>
                <div>
                  Elevation: {task.event_window.max_elevation_deg?.toFixed(1)}°
                </div>
                <div>
                  Status:{" "}
                  <span className={
                    task.validator_status === "passed"
                      ? "text-green-600"
                      : "text-yellow-600"
                  }>
                    {task.validator_status}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Stat Card
function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "green" | "orange" | "slate";
}) {
  const colorMap = {
    green: "bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400",
    orange: "bg-orange-100 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400",
    slate: "bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-400",
  };

  return (
    <div className={`p-3 rounded-lg ${colorMap[color]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs opacity-75">{label}</div>
    </div>
  );
}

export default ReplanModal;
