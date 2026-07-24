import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Download,
  Loader2,
  Play,
  ShieldAlert,
} from "lucide-react";

import { demoApi, tenancyApi } from "../lib/api";

export default function DemoReplayPage() {
  const [constellationId, setConstellationId] = useState("");
  const [satelliteId, setSatelliteId] = useState("");

  const constellations = useQuery({
    queryKey: ["constellations"],
    queryFn: () => tenancyApi.listConstellations(),
  });
  useEffect(() => {
    const demo =
      constellations.data?.find((item) => item.is_demo) ??
      constellations.data?.[0];
    if (!constellationId && demo) setConstellationId(demo.id);
  }, [constellationId, constellations.data]);

  const satellites = useQuery({
    queryKey: ["constellation-satellites", constellationId],
    queryFn: () => tenancyApi.listSatellites(constellationId),
    enabled: Boolean(constellationId),
  });
  useEffect(() => {
    if (!satelliteId && satellites.data?.length) {
      setSatelliteId(satellites.data[0].satellite.id);
    }
  }, [satelliteId, satellites.data]);

  const replay = useMutation({ mutationFn: demoApi.createReplay });
  const impact = useMutation({
    mutationFn: () =>
      demoApi.planningImpact(replay.data!.replay_id, {
        constellation_id: constellationId,
        satellite_id: satelliteId,
        unavailable_from_utc: "2024-06-01T11:30:00Z",
        unavailable_to_utc: "2024-06-01T12:30:00Z",
        reason: "synthetic_conjunction_what_if",
      }),
  });

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl bg-slate-950 p-7 text-white shadow-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300">
          Phase 0 decision demo
        </p>
        <div className="mt-4 grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
          <div>
            <h2 className="text-3xl font-semibold leading-tight sm:text-4xl">
              Replay a conjunction warning, then test its planning impact.
            </h2>
            <p className="mt-4 max-w-2xl text-slate-300">
              This five-minute path demonstrates data quality and schedule
              consequences. It does not calculate collision probability or
              recommend a maneuver.
            </p>
          </div>
          <div className="rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4">
            <div className="flex gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
              <p className="text-sm text-amber-100">
                Research and decision-support software. Not flight-certified.
                No maneuver is executed by Apex. Synthetic data only.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <StepCard number="1" title="Replay the event" active={!replay.data}>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Validate the committed fixture, provenance and canonical SHA-256.
          </p>
          <button
            onClick={() => replay.mutate()}
            disabled={replay.isPending}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-medium text-white disabled:opacity-50"
          >
            {replay.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            Run deterministic replay
          </button>
        </StepCard>

        <StepCard number="2" title="Apply a what-if window" active={Boolean(replay.data) && !impact.data}>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Constellation
          </label>
          <select
            value={constellationId}
            onChange={(event) => {
              setConstellationId(event.target.value);
              setSatelliteId("");
            }}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
          >
            {constellations.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <label className="mt-3 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Hypothetically unavailable satellite
          </label>
          <select
            value={satelliteId}
            onChange={(event) => setSatelliteId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
          >
            {satellites.data?.map((link) => (
              <option key={link.satellite.id} value={link.satellite.id}>
                {link.satellite.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => impact.mutate()}
            disabled={!replay.data || !satelliteId || impact.isPending}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-40 dark:bg-cyan-600"
          >
            {impact.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <ArrowRight className="h-5 w-5" />
            )}
            Compare schedule
          </button>
        </StepCard>

        <StepCard number="3" title="Export evidence" active={Boolean(impact.data)}>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Download the normalized replay with its provenance, hash, warnings,
            and explicit limitations.
          </p>
          <div className="mt-5 grid grid-cols-2 gap-2">
            {(["json", "md"] as const).map((format) => (
              <button
                key={format}
                disabled={!replay.data}
                onClick={() =>
                  replay.data &&
                  demoApi.exportReplay(replay.data.replay_id, format)
                }
                className="flex items-center justify-center gap-2 rounded-xl border border-slate-300 px-3 py-3 text-sm font-medium disabled:opacity-40 dark:border-slate-600"
              >
                <Download className="h-4 w-4" />
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </StepCard>
      </div>

      {(replay.error || impact.error) && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertTriangle className="mr-2 inline h-4 w-4" />
          {String((replay.error || impact.error)?.message)}
        </div>
      )}

      {replay.data && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {replay.data.event_id}
              </p>
              <h3 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                Provided risk, degraded evidence quality
              </h3>
            </div>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold uppercase text-amber-800">
              Pc provided · not computed
            </span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Time of closest approach" value="2024-06-01 12:00 UTC" />
            <Metric label="Miss distance" value={`${replay.data.relative_state.miss_distance_m} m`} />
            <Metric label="Relative speed" value={`${(replay.data.relative_state.relative_speed_m_s / 1000).toFixed(2)} km/s`} />
            <Metric label="Provided Pc" value={replay.data.risk.collision_probability.toExponential(2)} />
          </div>

          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <strong>Why quality is degraded:</strong>{" "}
            {replay.data.data_quality.explanation}
          </div>
          <p className="mt-4 break-all font-mono text-xs text-slate-500">
            fixture sha256: {replay.data.fixture_sha256}
          </p>
        </section>
      )}

      {impact.data && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
            <div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                Schedule comparison complete
              </h3>
              <p className="text-sm text-slate-500">
                Hypothetical availability effect, physics_verified=false
              </p>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
            <Metric label="Before" value={`${impact.data.before.task_count} planned task`} />
            <ArrowRight className="h-6 w-6 text-slate-400" />
            <Metric label="After" value={`${impact.data.after.task_count} planned task`} />
          </div>
          <ul className="mt-5 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            {impact.data.limitations.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
          <p className="mt-4 break-all font-mono text-xs text-slate-500">
            impact sha256: {impact.data.evidence_sha256}
          </p>
        </section>
      )}
    </div>
  );
}

function StepCard({
  number,
  title,
  active,
  children,
}: {
  number: string;
  title: string;
  active: boolean;
  children: ReactNode;
}) {
  return (
    <section
      className={`rounded-2xl border bg-white p-5 shadow-sm transition dark:bg-slate-800 ${
        active
          ? "border-blue-400 ring-4 ring-blue-100 dark:ring-blue-950"
          : "border-slate-200 dark:border-slate-700"
      }`}
    >
      <div className="mb-4 flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white dark:bg-blue-600">
          {number}
        </span>
        <h3 className="font-semibold text-slate-900 dark:text-white">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  );
}
