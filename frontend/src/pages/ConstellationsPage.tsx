import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Satellite, Trash2 } from "lucide-react";

import { satelliteApi, tenancyApi } from "../lib/api";

export default function ConstellationsPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: tenancyApi.listOrganizations,
  });
  const constellations = useQuery({
    queryKey: ["constellations"],
    queryFn: () => tenancyApi.listConstellations(),
  });
  const catalog = useQuery({
    queryKey: ["satellite-catalog"],
    queryFn: satelliteApi.catalog,
  });

  useEffect(() => {
    if (!selectedId && constellations.data?.length) {
      setSelectedId(constellations.data[0].id);
    }
  }, [constellations.data, selectedId]);

  const links = useQuery({
    queryKey: ["constellation-satellites", selectedId],
    queryFn: () => tenancyApi.listSatellites(selectedId),
    enabled: Boolean(selectedId),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      tenancyApi.createConstellation({
        organization_id: organizations.data![0].id,
        name,
        slug,
      }),
    onSuccess: (created) => {
      setName("");
      setSlug("");
      setSelectedId(created.id);
      queryClient.invalidateQueries({ queryKey: ["constellations"] });
    },
  });

  const attachMutation = useMutation({
    mutationFn: (satelliteId: string) =>
      tenancyApi.attachSatellite(selectedId, satelliteId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["constellation-satellites", selectedId],
      });
      queryClient.invalidateQueries({ queryKey: ["constellations"] });
    },
  });

  const detachMutation = useMutation({
    mutationFn: (satelliteId: string) =>
      tenancyApi.detachSatellite(selectedId, satelliteId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["constellation-satellites", selectedId],
      });
      queryClient.invalidateQueries({ queryKey: ["constellations"] });
    },
  });

  const selected = constellations.data?.find((item) => item.id === selectedId);
  const attachedIds = new Set(
    links.data?.map((link) => link.satellite.id) ?? [],
  );
  const canWrite = selected?.role === "owner" || selected?.role === "operator";

  const handleCreate = (event: FormEvent) => {
    event.preventDefault();
    if (!name || !slug || !organizations.data?.length) return;
    createMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <section>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
          Planning boundary
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
          Constellations
        </h2>
        <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
          A constellation is the explicit asset boundary for every plan. Adding
          a catalog satellite here does not claim ownership of the real
          spacecraft or create an operational orbit solution.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h3 className="font-semibold text-slate-900 dark:text-white">
            Your constellations
          </h3>
          <div className="mt-3 space-y-2">
            {constellations.isLoading && <Loader2 className="animate-spin" />}
            {constellations.data?.map((constellation) => (
              <button
                key={constellation.id}
                onClick={() => setSelectedId(constellation.id)}
                className={`w-full rounded-xl border p-3 text-left transition ${
                  selectedId === constellation.id
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                    : "border-slate-200 hover:border-slate-300 dark:border-slate-700"
                }`}
              >
                <span className="block font-medium text-slate-900 dark:text-white">
                  {constellation.name}
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  {constellation.satellite_count} satellites · {constellation.role}
                </span>
              </button>
            ))}
          </div>

          <form onSubmit={handleCreate} className="mt-5 border-t border-slate-200 pt-4 dark:border-slate-700">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Create an empty constellation
            </p>
            <input
              value={name}
              onChange={(event) => {
                setName(event.target.value);
                setSlug(
                  event.target.value
                    .toLowerCase()
                    .trim()
                    .replace(/[^a-z0-9]+/g, "-")
                    .replace(/^-|-$/g, ""),
                );
              }}
              placeholder="Mission sandbox"
              className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
            />
            <input
              value={slug}
              onChange={(event) => setSlug(event.target.value)}
              placeholder="mission-sandbox"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
            />
            <button
              disabled={!name || !slug || createMutation.isPending}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-blue-600"
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Create
            </button>
          </form>
        </aside>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          {selected ? (
            <>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                    {selected.name}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {selected.slug} · {selected.role}
                  </p>
                </div>
                {selected.is_demo && (
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                    Synthetic demo
                  </span>
                )}
              </div>

              <div className="mt-6">
                <h4 className="font-medium text-slate-900 dark:text-white">
                  Attached planning assets
                </h4>
                <div className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 dark:divide-slate-700 dark:border-slate-700">
                  {links.data?.map((link) => (
                    <div
                      key={link.satellite.id}
                      className="flex items-center justify-between gap-4 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <Satellite className="h-5 w-5 text-blue-500" />
                        <div>
                          <p className="font-medium text-slate-800 dark:text-slate-100">
                            {link.display_name || link.satellite.name}
                          </p>
                          <p className="text-xs text-slate-500">
                            Catalog {link.satellite.norad_id} · TLE epoch{" "}
                            {new Date(link.satellite.tle_epoch).toISOString()}
                          </p>
                        </div>
                      </div>
                      {canWrite && (
                        <button
                          onClick={() => detachMutation.mutate(link.satellite.id)}
                          aria-label={`Detach ${link.satellite.name}`}
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  {!links.isLoading && !links.data?.length && (
                    <p className="p-5 text-sm text-slate-500">
                      No satellites attached. Choose one from the demo catalog below.
                    </p>
                  )}
                </div>
              </div>

              {canWrite && (
                <div className="mt-8">
                  <h4 className="font-medium text-slate-900 dark:text-white">
                    Available demo catalog
                  </h4>
                  <p className="mt-1 text-sm text-slate-500">
                    Phase 0 supports attaching existing catalog records. Orbit
                    file upload arrives in a later phase.
                  </p>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    {catalog.data
                      ?.filter((satellite) => !attachedIds.has(satellite.id))
                      .map((satellite) => (
                        <button
                          key={satellite.id}
                          onClick={() => attachMutation.mutate(satellite.id)}
                          className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-left hover:border-blue-400 dark:border-slate-700"
                        >
                          <span>
                            <span className="block font-medium text-slate-800 dark:text-slate-100">
                              {satellite.name}
                            </span>
                            <span className="text-xs text-slate-500">
                              {satellite.payload_type} · {satellite.max_resolution_m} m
                            </span>
                          </span>
                          <Plus className="h-4 w-4 text-blue-500" />
                        </button>
                      ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-slate-500">Create or select a constellation.</p>
          )}
        </section>
      </div>
    </div>
  );
}
