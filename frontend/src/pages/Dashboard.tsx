import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Activity, AlertTriangle, Database, Gauge, Loader2, PlayCircle, TrendingUp } from "lucide-react";
import { api, getApiErrorMessage } from "@/services/api";
import type { ModelStatus } from "@/services/types";
import { StatCard } from "@/components/shared/StatCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TimeSeriesChart } from "@/components/charts/Charts";
import { formatDateTime, formatInt, formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

type DemoStep =
  | { kind: "idle" }
  | { kind: "import" }
  | { kind: "train"; progress: number; epoch?: number | null; total?: number | null }
  | { kind: "detect" }
  | { kind: "done" }
  | { kind: "error"; message: string };

export default function Dashboard() {
  const qc = useQueryClient();

  const summary = useQuery({ queryKey: ["dashboard"], queryFn: () => api.dashboard() });
  const samples = useQuery({ queryKey: ["samples"], queryFn: () => api.listSamples() });
  const sources = useQuery({ queryKey: ["sources"], queryFn: () => api.sources() });

  // Pick first source for charts
  const firstSource = sources.data?.[0];
  const chartQuery = useQuery({
    queryKey: ["dashboard-chart", firstSource?.source_file, firstSource?.sensor_type],
    queryFn: () =>
      api.listData({
        source_file: firstSource!.source_file,
        sensor_type: firstSource!.sensor_type,
        limit: 500,
      }),
    enabled: !!firstSource,
  });

  const recentAnoms = useQuery({
    queryKey: ["recent-anomalies", firstSource?.source_file, firstSource?.sensor_type],
    queryFn: () =>
      api.results({
        source_file: firstSource!.source_file,
        sensor_type: firstSource!.sensor_type,
        limit: 500,
      }),
    enabled: !!firstSource,
  });

  const [selectedSample, setSelectedSample] = useState<string | undefined>();
  useEffect(() => {
    if (!selectedSample && samples.data && samples.data.length > 0) {
      setSelectedSample(samples.data[0].file_name);
    }
  }, [samples.data, selectedSample]);

  const [demo, setDemo] = useState<DemoStep>({ kind: "idle" });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  async function pollUntilDone(signal: AbortSignal): Promise<ModelStatus> {
    return new Promise((resolve, reject) => {
      let timer: ReturnType<typeof setTimeout>;
      const onAbort = () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      };
      signal.addEventListener("abort", onAbort, { once: true });
      const tick = async () => {
        try {
          const s = await api.status();
          if (signal.aborted) return;
          setDemo({ kind: "train", progress: s.progress ?? 0, epoch: s.current_epoch, total: s.total_epochs });
          if (s.state === "completed") return resolve(s);
          if (s.state === "failed") return reject(new Error(s.message ?? "Model o'qitishda xatolik"));
          timer = setTimeout(tick, 2000);
        } catch (e) {
          reject(e);
        }
      };
      tick();
    });
  }

  const runDemo = useMutation({
    mutationFn: async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (!selectedSample) throw new Error("Sample tanlanmagan");
      const sample = samples.data?.find((s) => s.file_name === selectedSample);
      if (!sample) throw new Error("Sample topilmadi");

      setDemo({ kind: "import" });
      const imported = await api.importSample({ file_name: sample.file_name, sensor_type: sample.sensor_type });

      setDemo({ kind: "train", progress: 0 });
      await api.train({
        sensor_type: imported.sensor_type,
        source_file: imported.source_file,
        epochs: 20,
      });
      await pollUntilDone(controller.signal);

      setDemo({ kind: "detect" });
      await api.detect({ sensor_type: imported.sensor_type, source_file: imported.source_file });

      setDemo({ kind: "done" });
      return imported;
    },
    onSuccess: () => {
      toast.success("Demo yakunlandi");
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["sources"] });
      qc.invalidateQueries({ queryKey: ["dashboard-chart"] });
      qc.invalidateQueries({ queryKey: ["recent-anomalies"] });
    },
    onError: (err) => {
      const msg = getApiErrorMessage(err);
      setDemo({ kind: "error", message: msg });
      toast.error(msg);
    },
  });

  const chartData = useMemo(() => {
    const items = chartQuery.data?.items ?? [];
    const anomalyMap = new Map<number, boolean>();
    (recentAnoms.data?.items ?? []).forEach((a) => anomalyMap.set(a.sensor_data_id, a.is_anomaly));
    return [...items]
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map((d) => ({ ts: d.timestamp, value: d.value, isAnomaly: anomalyMap.get(d.id) ?? false }));
  }, [chartQuery.data, recentAnoms.data]);

  const recentTrueAnomalies = useMemo(
    () => (recentAnoms.data?.items ?? []).filter((item) => item.is_anomaly).slice(0, 8),
    [recentAnoms.data],
  );

  const s = summary.data;

  return (
    <div className="space-y-4 max-w-[1400px] mx-auto w-full">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <h1 className="font-display text-xl font-semibold">Dashboard</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>{s?.sensor_types?.length ? s.sensor_types.join(", ") : "Sensor yo'q"}</span>
            <span>•</span>
            <span>{formatDateTime(s?.latest_anomaly)}</span>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Select value={selectedSample} onValueChange={setSelectedSample} disabled={runDemo.isPending || samples.isLoading}>
            <SelectTrigger className="w-full sm:w-[260px]">
              <SelectValue placeholder="Sample" />
            </SelectTrigger>
            <SelectContent>
              {(samples.data ?? []).map((sample) => (
                <SelectItem key={sample.file_name} value={sample.file_name}>
                  {sample.file_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => runDemo.mutate()} disabled={!selectedSample || runDemo.isPending}>
            {runDemo.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <PlayCircle className="h-4 w-4 mr-2" />}
            Demo
          </Button>
        </div>
      </header>

      {demo.kind !== "idle" && (
        <section className="surface-card px-4 py-3">
          <DemoProgress step={demo} />
        </section>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          label="Data"
          value={formatInt(s?.total_sensor_data)}
          icon={<Database className="h-4 w-4" />}
          tone="teal"
          loading={summary.isLoading}
        />
        <StatCard
          label="Anomaliya"
          value={formatInt(s?.total_anomalies)}
          icon={<AlertTriangle className="h-4 w-4" />}
          tone="danger"
          loading={summary.isLoading}
        />
        <StatCard
          label="Rate"
          value={s ? formatPercent(s.anomaly_percentage, 2) : "—"}
          icon={<TrendingUp className="h-4 w-4" />}
          tone="amber"
          loading={summary.isLoading}
        />
        <StatCard
          label="F1"
          value={s?.latest_model ? formatNumber(s.latest_model.f1, 3) : "—"}
          hint={s?.latest_model ? s.latest_model.name : "Model hali o'qitilmagan"}
          icon={<Gauge className="h-4 w-4" />}
          tone="primary"
          loading={summary.isLoading}
        />
      </div>

      {/* Time series + Recent anomalies */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 lg:gap-6">
        <SectionCard
          className="xl:col-span-2"
          title="Signal"
          description={
            firstSource
              ? `${firstSource.source_file} · ${firstSource.sensor_type}`
              : "Birinchi mavjud datasetdan namuna"
          }
        >
          {chartQuery.isLoading ? (
            <Skeleton className="h-[280px] w-full" />
          ) : chartData.length === 0 ? (
            <EmptyState
              title="Ma'lumot yo'q"
              icon={<Database className="h-5 w-5" />}
            />
          ) : (
            <TimeSeriesChart data={chartData} showAnomalies />
          )}
        </SectionCard>

        <SectionCard title="Anomaliyalar">
          {recentAnoms.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : recentTrueAnomalies.length === 0 ? (
            <EmptyState
              title="Anomaliya topilmadi"
              icon={<Activity className="h-5 w-5" />}
            />
          ) : (
            <ul className="divide-y divide-border/60 -mx-2">
              {recentTrueAnomalies.map((a) => (
                <li key={a.id} className="flex items-center justify-between gap-3 px-2 py-2.5">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{a.sensor_type}</div>
                    <div className="text-[11px] text-muted-foreground">{formatDateTime(a.timestamp)}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono text-xs tabular-nums">{formatNumber(a.value, 3)}</div>
                    <div className="font-mono text-[10px] text-muted-foreground tabular-nums">
                      {formatNumber(a.severity_score, 2)}x
                    </div>
                    <Badge
                      variant="destructive"
                      className={cn(
                        "mt-0.5 text-[10px] px-1.5 py-0",
                        "bg-destructive-soft text-destructive border-destructive/30 hover:bg-destructive-soft"
                      )}
                    >
                      Anomaliya
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

function DemoProgress({ step }: { step: DemoStep }) {
  if (step.kind === "idle") {
    return (
      <p className="text-sm text-muted-foreground">Import → Model → Tahlil</p>
    );
  }
  if (step.kind === "error") {
    return <div className="text-sm text-destructive">{step.message}</div>;
  }
  const stages = [
    { id: "import", label: "Import" },
    { id: "train", label: "Model" },
    { id: "detect", label: "Tahlil" },
    { id: "done", label: "Tayyor" },
  ];
  const currentIdx = stages.findIndex((s) => s.id === step.kind);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
        {stages.map((s, i) => {
          const active = i === currentIdx;
          const done = i < currentIdx || step.kind === "done";
          return (
            <div
              key={s.id}
              className={cn(
                "rounded-xl border px-3 py-2.5 text-xs font-medium transition-colors",
                done && "bg-accent text-accent-foreground border-sage/30",
                active && "bg-primary-soft text-primary border-primary/30",
                !active && !done && "bg-muted text-muted-foreground border-border"
              )}
            >
              <div className="flex items-center gap-2">
                {active && <Loader2 className="h-3 w-3 animate-spin" />}
                <span>{s.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {step.kind === "train" && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Epoch {step.epoch ?? 0}
              {step.total ? ` / ${step.total}` : ""}
            </span>
            <span className="tabular-nums">{Math.min(100, Math.max(0, step.progress))}%</span>
          </div>
          <Progress value={Math.min(100, Math.max(0, step.progress))} />
        </div>
      )}
    </div>
  );
}
