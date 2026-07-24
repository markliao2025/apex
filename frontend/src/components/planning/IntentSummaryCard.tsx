/**
 * IntentSummaryCard Component — Display parsed planning intent
 */

import { MapPin, Target, Clock, Zap, Eye, AlertTriangle, CheckCircle2 } from "lucide-react";
import type { ElementType } from "react";

interface IntentSummaryCardProps {
  intent: {
    region_description?: string | null;
    resolution_requirement_m?: number | null;
    time_window_days?: number | null;
    priority: string;
    event_filter?: string | null;
    sensor_preference?: string | null;
    uncertainty_notes?: string[];
  };
  status: string;
  rawInput: string;
  confidence?: Record<string, number>;
}

type ColorKey = "blue" | "green" | "orange" | "red" | "slate";

const PRIORITY_CONFIG: Record<string, { color: ColorKey; icon: string }> = {
  low: { color: "slate", icon: "📋" },
  normal: { color: "blue", icon: "📝" },
  high: { color: "orange", icon: "🔥" },
  urgent: { color: "red", icon: "🚨" },
};

const COLOR_CLASSES = {
  blue: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30",
  green: "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30",
  orange: "text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/30",
  red: "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30",
  slate: "text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700",
};

const ICON_CLASSES = {
  blue: "text-blue-500",
  green: "text-green-500",
  orange: "text-orange-500",
  red: "text-red-500",
  slate: "text-slate-500",
};

export function IntentSummaryCard({
  intent,
  status,
  rawInput,
  confidence,
}: IntentSummaryCardProps) {
  const priorityKey = intent.priority as keyof typeof PRIORITY_CONFIG;
  const priorityConfig = PRIORITY_CONFIG[priorityKey] || PRIORITY_CONFIG.normal;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg">
            <Target className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white">
              Intent Summary
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 truncate max-w-md">
              {rawInput}
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <StatusBadge status={status} />
      </div>

      {/* Main Info Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <InfoItem
          icon={MapPin}
          label="Region"
          value={intent.region_description || "Not specified"}
        />
        <InfoItem
          icon={Target}
          label="Resolution"
          value={
            intent.resolution_requirement_m
              ? `≤${intent.resolution_requirement_m}m`
              : "Any"
          }
        />
        <InfoItem
          icon={Clock}
          label="Time Window"
          value={
            intent.time_window_days
              ? `${intent.time_window_days} day${intent.time_window_days !== 1 ? "s" : ""}`
              : "Default"
          }
        />
        <InfoItem
          icon={Zap}
          label="Priority"
          value={intent.priority.toUpperCase()}
          color={priorityConfig.color}
        />
        <InfoItem
          icon={Eye}
          label="Event"
          value={intent.event_filter || "None"}
        />
        <InfoItem
          icon={Target}
          label="Sensor"
          value={intent.sensor_preference || "Any"}
        />
      </div>

      {/* Confidence Scores */}
      {confidence && Object.keys(confidence).length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">
            Confidence Scores
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(confidence).map(([key, value]) => (
              <ConfidenceBar
                key={key}
                label={formatLabel(key)}
                value={value as number}
              />
            ))}
          </div>
        </div>
      )}

      {/* Uncertainty Notes */}
      {intent.uncertainty_notes && intent.uncertainty_notes.length > 0 && (
        <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
                Clarifications Needed
              </p>
              <ul className="text-sm text-amber-600 dark:text-amber-500 list-disc list-inside space-y-0.5">
                {intent.uncertainty_notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* All Fields Parsed Successfully */}
      {(!intent.uncertainty_notes || intent.uncertainty_notes.length === 0) && (
        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
            <p className="text-sm text-green-700 dark:text-green-400">
              All fields successfully parsed from your request
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Info Item Component
function InfoItem({
  icon: Icon,
  label,
  value,
  color = "blue",
}: {
  icon: ElementType;
  label: string;
  value: string;
  color?: "blue" | "green" | "red" | "orange" | "slate";
}) {
  const iconClass = ICON_CLASSES[color] ?? ICON_CLASSES.blue;
  const valueClass = COLOR_CLASSES[color] ?? COLOR_CLASSES.blue;

  return (
    <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`w-4 h-4 ${iconClass}`} />
        <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className={`font-medium text-sm truncate ${valueClass}`}>
        {value}
      </p>
    </div>
  );
}

// Confidence Bar Component
function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);

  const barColor =
    value >= 0.8
      ? "bg-green-500"
      : value >= 0.5
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-600 dark:text-slate-400">{label}</span>
        <span className={`font-medium ${
          value >= 0.8
            ? "text-green-600 dark:text-green-400"
            : value >= 0.5
            ? "text-yellow-600 dark:text-yellow-400"
            : "text-red-600 dark:text-red-400"
        }`}>
          {percentage}%
        </span>
      </div>
      <div className="h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { color: string; icon: ElementType; text: string }> = {
    ready: { color: "green", icon: CheckCircle2, text: "Ready" },
    planning: { color: "blue", icon: Clock, text: "Planning" },
    pending: { color: "yellow", icon: Clock, text: "Pending" },
    partial: { color: "orange", icon: AlertTriangle, text: "Partial" },
    failed: { color: "red", icon: AlertTriangle, text: "Failed" },
    planning_error: { color: "red", icon: AlertTriangle, text: "Error" },
    cancelled: { color: "slate", icon: AlertTriangle, text: "Cancelled" },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${COLOR_CLASSES[config.color as keyof typeof COLOR_CLASSES]}`}
    >
      <config.icon className="w-4 h-4" />
      {config.text}
    </span>
  );
}

// Helper function to format label
function formatLabel(key: string): string {
  const labelMap: Record<string, string> = {
    region_description: "Region",
    resolution_requirement_m: "Resolution",
    time_window_days: "Time Window",
    priority: "Priority",
    event_filter: "Event",
    sensor_preference: "Sensor",
    confidence: "Confidence",
  };
  return labelMap[key] || key;
}

export default IntentSummaryCard;
