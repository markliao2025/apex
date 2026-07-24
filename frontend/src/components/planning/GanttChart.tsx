/**
 * GanttChart Component — Satellite Task Timeline Visualization
 *
 * Features:
 * - Time-based horizontal bars for each satellite
 * - Task duration visualization
 * - Elevation and validation status indicators
 * - Zoom and pan controls
 * - Time range adjustment
 */

import { useState, useMemo, useCallback } from "react";
import { ChevronLeft, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

interface GanttTask {
  id: string;
  satellite_id: string;
  satellite_name?: string | null;
  event_window: {
    aos_time: string;
    los_time: string;
    max_elevation_deg: number;
  };
  validator_status: string;
  resource_allocation: {
    battery_delta_percent: number;
    storage_mb: number;
  };
}

interface GanttChartProps {
  tasks: GanttTask[];
  satellites: { id: string; name: string }[];
  /** Time range in hours, default 24 */
  defaultRangeHours?: number;
  /** Callback when task is clicked */
  onTaskClick?: (task: GanttTask) => void;
  /** Selected task ID */
  selectedTaskId?: string;
}

const SATELLITE_COLORS = [
  { bg: "bg-blue-500", hover: "bg-blue-600", light: "bg-blue-100" },
  { bg: "bg-green-500", hover: "bg-green-600", light: "bg-green-100" },
  { bg: "bg-orange-500", hover: "bg-orange-600", light: "bg-orange-100" },
  { bg: "bg-purple-500", hover: "bg-purple-600", light: "bg-purple-100" },
  { bg: "bg-pink-500", hover: "bg-pink-600", light: "bg-pink-100" },
  { bg: "bg-cyan-500", hover: "bg-cyan-600", light: "bg-cyan-100" },
  { bg: "bg-indigo-500", hover: "bg-indigo-600", light: "bg-indigo-100" },
  { bg: "bg-teal-500", hover: "bg-teal-600", light: "bg-teal-100" },
];

export function GanttChart({
  tasks,
  satellites,
  defaultRangeHours = 24,
  onTaskClick,
  selectedTaskId,
}: GanttChartProps) {
  const [zoomLevel, setZoomLevel] = useState(1);

  // Group tasks by satellite
  const groupedTasks = useMemo(() => {
    const grouped = new Map<string, GanttTask[]>();

    for (const task of tasks) {
      const sat = satellites.find((s) => s.id === task.satellite_id);
      const satName = sat?.name || task.satellite_id.substring(0, 8);

      if (!grouped.has(satName)) {
        grouped.set(satName, []);
      }
      grouped.get(satName)!.push(task);
    }

    return grouped;
  }, [tasks, satellites]);

  // Calculate time range
  const timeRange = useMemo(() => {
    if (tasks.length === 0) {
      const now = Date.now();
      return { start: now, end: now + defaultRangeHours * 60 * 60 * 1000 };
    }

    const starts = tasks.map((t) => new Date(t.event_window.aos_time).getTime());
    const ends = tasks.map((t) => new Date(t.event_window.los_time).getTime());

    const minTime = Math.min(...starts);
    const maxTime = Math.max(...ends);

    // Add padding
    const padding = (maxTime - minTime) * 0.1 || defaultRangeHours * 60 * 60 * 1000;
    return {
      start: minTime - padding,
      end: maxTime + padding,
    };
  }, [tasks, defaultRangeHours]);

  // Generate time ticks
  const timeTicks = useMemo(() => {
    const ticks: { time: number; label: string; isMajor: boolean }[] = [];
    const totalMs = timeRange.end - timeRange.start;
    const tickInterval = calculateTickInterval(totalMs / zoomLevel);

    let current = Math.ceil(timeRange.start / tickInterval) * tickInterval;
    while (current <= timeRange.end) {
      const date = new Date(current);
      ticks.push({
        time: current,
        label: formatTickLabel(date, tickInterval),
        isMajor: isMajorTick(date, tickInterval),
      });
      current += tickInterval;
    }

    return ticks;
  }, [timeRange, zoomLevel]);

  // Get satellite color
  const getSatelliteColor = useCallback((_satName: string, index: number) => {
    return SATELLITE_COLORS[index % SATELLITE_COLORS.length];
  }, []);

  // Calculate bar position and width
  const calculateBarStyle = useCallback((task: GanttTask) => {
    const start = new Date(task.event_window.aos_time).getTime();
    const end = new Date(task.event_window.los_time).getTime();

    const left = ((start - timeRange.start) / (timeRange.end - timeRange.start)) * 100;
    const width = ((end - start) / (timeRange.end - timeRange.start)) * 100;

    return {
      left: `${Math.max(0, left)}%`,
      width: `${Math.max(0.5, width)}%`,
    };
  }, [timeRange]);

  // Handle zoom
  const handleZoomIn = () => setZoomLevel((z) => Math.min(z * 1.5, 10));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z / 1.5, 0.5));
  const handleReset = () => {
    setZoomLevel(1);
  };

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 dark:text-slate-500">
        <div className="text-center">
          <div className="text-4xl mb-2">📅</div>
          <p>No tasks to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="gantt-chart bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Task Timeline
        </h4>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {}}
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition"
            title="Scroll left"
          >
            <ChevronLeft className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
          <span className="text-xs text-slate-500 dark:text-slate-400 min-w-[3rem] text-center">
            {Math.round(zoomLevel * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition"
            title="Reset view"
          >
            <Maximize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4">
        {Array.from(groupedTasks.entries()).map(([satName], idx) => {
          const colors = getSatelliteColor(satName, idx);
          return (
            <div key={satName} className="flex items-center gap-1.5">
              <span className={`w-3 h-3 rounded ${colors.bg}`} />
              <span className="text-xs text-slate-600 dark:text-slate-400">{satName}</span>
            </div>
          );
        })}
      </div>

      {/* Chart Container */}
      <div className="overflow-x-auto">
        <div
          className="min-w-full"
          style={{ transform: `scaleX(${zoomLevel})`, transformOrigin: "left" }}
        >
          {/* Time Axis */}
          <div className="flex border-b border-slate-200 dark:border-slate-600 pb-1 mb-2">
            <div className="w-28 flex-shrink-0" />
            <div className="flex-1 relative">
              {timeTicks.map((tick, idx) => (
                <div
                  key={idx}
                  className="absolute text-[10px] text-slate-400 dark:text-slate-500"
                  style={{
                    left: `${((tick.time - timeRange.start) / (timeRange.end - timeRange.start)) * 100}%`,
                    transform: "translateX(-50%)",
                  }}
                >
                  {tick.isMajor && (
                    <div className="w-px h-2 bg-slate-300 dark:bg-slate-600 absolute -bottom-2 left-1/2 -translate-x-1/2" />
                  )}
                  {tick.label}
                </div>
              ))}
            </div>
          </div>

          {/* Rows */}
          <div className="space-y-3">
            {Array.from(groupedTasks.entries()).map(([satName, satTasks], satIdx) => {
              const colors = getSatelliteColor(satName, satIdx);

              return (
                <div key={satName} className="flex items-center">
                  {/* Satellite Label */}
                  <div className="w-28 flex-shrink-0 pr-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded ${colors.bg}`} />
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate" title={satName}>
                        {satName}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 truncate pl-4">
                      {satTasks.length} task{satTasks.length !== 1 ? "s" : ""}
                    </div>
                  </div>

                  {/* Timeline Track */}
                  <div className="flex-1 relative h-10 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-600">
                    {/* Grid lines */}
                    {timeTicks.filter(t => t.isMajor).map((tick, idx) => (
                      <div
                        key={idx}
                        className="absolute top-0 bottom-0 w-px bg-slate-100 dark:bg-slate-700"
                        style={{
                          left: `${((tick.time - timeRange.start) / (timeRange.end - timeRange.start)) * 100}%`,
                        }}
                      />
                    ))}

                    {/* Task Bars */}
                    {satTasks.map((task) => {
                      const style = calculateBarStyle(task);
                      const isSelected = task.id === selectedTaskId;
                      const isPassed = task.validator_status === "passed";

                      return (
                        <button
                          key={task.id}
                          onClick={() => onTaskClick?.(task)}
                          className={`
                            absolute top-1 h-8 rounded-md text-white text-[10px] font-medium
                            flex items-center px-2 overflow-hidden cursor-pointer
                            transition-all shadow-sm
                            ${colors.bg} hover:${colors.hover}
                            ${isSelected ? "ring-2 ring-offset-2 ring-blue-500" : ""}
                            ${!isPassed ? "opacity-80" : ""}
                          `}
                          style={style}
                          title={`${new Date(task.event_window.aos_time).toLocaleString()} - ${new Date(task.event_window.los_time).toLocaleString()}\nElevation: ${task.event_window.max_elevation_deg.toFixed(1)}°`}
                        >
                          <span className="truncate flex items-center gap-1">
                            {isPassed ? (
                              <span className="text-green-200">✓</span>
                            ) : (
                              <span className="text-yellow-200">⚠</span>
                            )}
                            <span className="hidden sm:inline">
                              {formatTime(new Date(task.event_window.aos_time))}
                            </span>
                            <span className="hidden md:inline opacity-75">
                              • {task.event_window.max_elevation_deg.toFixed(0)}°
                            </span>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-600 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>
          {tasks.length} task{tasks.length !== 1 ? "s" : ""} across {groupedTasks.size} satellite{groupedTasks.size !== 1 ? "s" : ""}
        </span>
        <span>
          {formatDateRange(timeRange.start, timeRange.end)}
        </span>
      </div>
    </div>
  );
}

// Helper functions
function calculateTickInterval(totalMs: number): number {
  const hourMs = 60 * 60 * 1000;
  const dayMs = 24 * hourMs;

  if (totalMs <= 6 * hourMs) return hourMs / 2; // 30 min
  if (totalMs <= 12 * hourMs) return hourMs; // 1 hour
  if (totalMs <= 2 * dayMs) return 2 * hourMs; // 2 hours
  if (totalMs <= 7 * dayMs) return 6 * hourMs; // 6 hours
  return dayMs; // 1 day
}

function formatTickLabel(date: Date, intervalMs: number): string {
  const hourMs = 60 * 60 * 1000;
  const dayMs = 24 * hourMs;

  if (intervalMs < hourMs) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  if (intervalMs < dayMs) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function isMajorTick(date: Date, intervalMs: number): boolean {
  const hourMs = 60 * 60 * 1000;

  if (intervalMs < hourMs) {
    return date.getMinutes() === 0;
  }
  if (intervalMs < 6 * hourMs) {
    return date.getHours() === 0;
  }
  return true;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDateRange(start: number, end: number): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const sameDay = startDate.toDateString() === endDate.toDateString();

  if (sameDay) {
    return `${startDate.toLocaleDateString([], { month: "short", day: "numeric" })} ${formatTime(startDate)} - ${formatTime(endDate)}`;
  }
  return `${startDate.toLocaleDateString([], { month: "short", day: "numeric" })} - ${endDate.toLocaleDateString([], { month: "short", day: "numeric" })}`;
}

export default GanttChart;
