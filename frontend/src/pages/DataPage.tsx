import { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  Database,
  Download,
  FileSpreadsheet,
  Loader2,
  Trash2,
  Upload,
} from "lucide-react";
import { api, getApiErrorMessage } from "@/services/api";
import { SectionCard } from "@/components/shared/SectionCard";
import { StatCard } from "@/components/shared/StatCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatBytes, formatDateTime, formatInt, formatNumber } from "@/lib/format";
import { cn, sourceKey } from "@/lib/utils";

const ALL = "__all__";

export default function DataPage() {
  const qc = useQueryClient();

  const sensors = useQuery({ queryKey: ["sensors"], queryFn: () => api.sensors() });
  const sources = useQuery({ queryKey: ["sources"], queryFn: () => api.sources() });
  const samples = useQuery({ queryKey: ["samples"], queryFn: () => api.listSamples() });

  const [sensorType, setSensorType] = useState<string>(ALL);
  const [sourceKeyValue, setSourceKeyValue] = useState<string>(ALL);
  const [page, setPage] = useState(0);
  const limit = 25;

  const selectedSource = useMemo(
    () => (sourceKeyValue === ALL ? undefined : sources.data?.find((s) => sourceKey(s.sensor_type, s.source_file) === sourceKeyValue)),
    [sourceKeyValue, sources.data]
  );

  const filterParams = {
    sensor_type: selectedSource?.sensor_type ?? (sensorType === ALL ? undefined : sensorType),
    source_file: selectedSource?.source_file,
  };

  const dataQ = useQuery({
    queryKey: ["data-list", filterParams, page],
    queryFn: () => api.listData({ ...filterParams, limit, offset: page * limit }),
  });

  const statsQ = useQuery({
    queryKey: ["data-stats", filterParams],
    queryFn: () => api.stats(filterParams),
  });

  const filteredSources = useMemo(() => {
    if (sensorType === ALL) return sources.data ?? [];
    return (sources.data ?? []).filter((s) => s.sensor_type === sensorType);
  }, [sources.data, sensorType]);

  // Upload
  const [uploadSensor, setUploadSensor] = useState("");
  const upload = useMutation({
    mutationFn: ({ file, st }: { file: File; st: string }) => api.uploadCsv(file, st || undefined),
    onSuccess: (res) => {
      toast.success(`Yuklandi: ${res.rows_inserted} qator (${res.sensor_type})`);
      qc.invalidateQueries({ queryKey: ["sensors"] });
      qc.invalidateQueries({ queryKey: ["sources"] });
      qc.invalidateQueries({ queryKey: ["data-list"] });
      qc.invalidateQueries({ queryKey: ["data-stats"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const dropzone = useDropzone({
    accept: { "text/csv": [".csv"] },
    multiple: false,
    onDrop: (files) => {
      if (files[0]) upload.mutate({ file: files[0], st: uploadSensor.trim() });
    },
  });

  // Sample import
  const [sampleFile, setSampleFile] = useState<string | undefined>();
  const importSample = useMutation({
    mutationFn: () => {
      const s = samples.data?.find((x) => x.file_name === sampleFile);
      if (!s) throw new Error("Sample tanlanmagan");
      return api.importSample({ file_name: s.file_name, sensor_type: s.sensor_type });
    },
    onSuccess: (r) => {
      toast.success(`Sample import: ${r.rows_inserted} qator`);
      qc.invalidateQueries({ queryKey: ["sensors"] });
      qc.invalidateQueries({ queryKey: ["sources"] });
      qc.invalidateQueries({ queryKey: ["data-list"] });
      qc.invalidateQueries({ queryKey: ["data-stats"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  // Delete
  const [confirm, setConfirm] = useState<{ kind: "source" | "sensor"; key: string; sensor_type?: string } | null>(null);
  const del = useMutation({
    mutationFn: () => {
      if (!confirm) throw new Error("");
      return confirm.kind === "source" ? api.deleteSource(confirm.key, confirm.sensor_type) : api.deleteSensor(confirm.key);
    },
    onSuccess: () => {
      toast.success("O'chirildi");
      setConfirm(null);
      setSourceKeyValue(ALL);
      qc.invalidateQueries({ queryKey: ["sensors"] });
      qc.invalidateQueries({ queryKey: ["sources"] });
      qc.invalidateQueries({ queryKey: ["data-list"] });
      qc.invalidateQueries({ queryKey: ["data-stats"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  // Export
  const [exporting, setExporting] = useState(false);
  async function onExport() {
    try {
      setExporting(true);
      await api.exportData(filterParams);
      toast.success("CSV yuklab olindi");
    } catch (e) {
      toast.error(getApiErrorMessage(e));
    } finally {
      setExporting(false);
    }
  }

  const total = dataQ.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto w-full">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-semibold">Ma'lumotlar</h1>
        </div>
        <Button variant="outline" onClick={onExport} disabled={exporting || total === 0}>
          {exporting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
          Eksport
        </Button>
      </header>

      {/* Upload + Sample import */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        <SectionCard
          className="lg:col-span-2"
          title="CSV"
        >
          <div className="grid gap-3 sm:grid-cols-[1fr,200px]">
            <div
              {...dropzone.getRootProps()}
              className={cn(
                "rounded-lg border-2 border-dashed transition-colors p-5 sm:p-6 text-center cursor-pointer",
                "hover:bg-muted/40 hover:border-primary/40",
                dropzone.isDragActive ? "border-primary bg-primary-soft/40" : "border-border"
              )}
            >
              <input {...dropzone.getInputProps()} />
              <div className="mx-auto h-9 w-9 rounded-md bg-primary-soft text-primary flex items-center justify-center mb-3">
                {upload.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
              </div>
              <div className="font-medium">CSV tanlang</div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="upload-sensor" className="text-xs">
                Sensor
              </Label>
              <Input
                id="upload-sensor"
                placeholder="temperature"
                value={uploadSensor}
                onChange={(e) => setUploadSensor(e.target.value)}
              />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Sample">
          <div className="space-y-3">
            <Select value={sampleFile} onValueChange={setSampleFile} disabled={samples.isLoading}>
              <SelectTrigger>
                <SelectValue placeholder="Sample tanlang" />
              </SelectTrigger>
              <SelectContent>
                {(samples.data ?? []).map((s) => (
                  <SelectItem key={s.file_name} value={s.file_name}>
                    {s.file_name}{" "}
                    <span className="text-muted-foreground text-xs ml-1">
                      · {s.sensor_type} · {formatBytes(s.size_bytes)}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={() => importSample.mutate()} disabled={!sampleFile || importSample.isPending} className="w-full">
              {importSample.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileSpreadsheet className="h-4 w-4 mr-2" />
              )}
              Import
            </Button>
          </div>
        </SectionCard>
      </div>

      {/* Filters + Stats */}
      <SectionCard title="Filter">
        <div className="grid gap-4 lg:grid-cols-[280px,1fr]">
          <div className="space-y-3">
            <div>
              <Label className="text-xs">Sensor</Label>
              <Select
                value={sensorType}
                onValueChange={(v) => {
                  setSensorType(v);
                  setSourceKeyValue(ALL);
                  setPage(0);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Barchasi</SelectItem>
                  {(sensors.data ?? []).map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs">Dataset</Label>
              <Select
                value={sourceKeyValue}
                onValueChange={(v) => {
                  setSourceKeyValue(v);
                  setPage(0);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Barchasi</SelectItem>
                  {filteredSources.map((s) => (
                    <SelectItem key={sourceKey(s.sensor_type, s.source_file)} value={sourceKey(s.sensor_type, s.source_file)}>
                      {s.source_file}
                      <span className="text-muted-foreground text-xs ml-1">· {formatInt(s.rows_count)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-2 pt-2">
              <Button
                variant="outline"
                disabled={!selectedSource}
                onClick={() =>
                  selectedSource &&
                  setConfirm({
                    kind: "source",
                    key: selectedSource.source_file,
                    sensor_type: selectedSource.sensor_type,
                  })
                }
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                O'chirish
              </Button>
              <Button
                variant="outline"
                disabled={sensorType === ALL || selectedSource !== undefined}
                onClick={() => sensorType !== ALL && setConfirm({ kind: "sensor", key: sensorType })}
                className="text-destructive hover:text-destructive"
                title={selectedSource ? "Sensor o'chirish uchun datasetni tozalang" : ""}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Sensor
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <StatCard label="Yozuvlar" value={formatInt(statsQ.data?.count)} loading={statsQ.isLoading} tone="teal" />
            <StatCard label="O'rtacha" value={formatNumber(statsQ.data?.mean, 4)} loading={statsQ.isLoading} />
            <StatCard label="Std" value={formatNumber(statsQ.data?.std, 4)} loading={statsQ.isLoading} />
            <StatCard label="Min" value={formatNumber(statsQ.data?.min, 4)} loading={statsQ.isLoading} tone="sage" />
            <StatCard label="Max" value={formatNumber(statsQ.data?.max, 4)} loading={statsQ.isLoading} tone="amber" />
          </div>
        </div>
      </SectionCard>

      {/* Data table */}
      <SectionCard
        title="Jadval"
        description={total > 0 ? `${formatInt(total)} qator` : ""}
        actions={
          total > 0 && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
                Oldingi
              </Button>
              <span className="tabular-nums">
                {page + 1} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Keyingi
              </Button>
            </div>
          )
        }
        bodyClassName="p-0"
      >
        {dataQ.isLoading ? (
          <div className="p-6 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (dataQ.data?.items?.length ?? 0) === 0 ? (
              <EmptyState title="Ma'lumot yo'q" icon={<Database className="h-5 w-5" />} />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">ID</TableHead>
                  <TableHead>Vaqt</TableHead>
                  <TableHead className="text-right">Qiymat</TableHead>
                  <TableHead>Sensor</TableHead>
                  <TableHead>Dataset</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dataQ.data!.items.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">{d.id}</TableCell>
                    <TableCell className="whitespace-nowrap">{formatDateTime(d.timestamp)}</TableCell>
                    <TableCell className="text-right font-mono tabular-nums">{formatNumber(d.value, 4)}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-secondary text-secondary-foreground">
                        {d.sensor_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground truncate max-w-[240px]">
                      {d.source_file}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </SectionCard>

      <AlertDialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>O'chirishni tasdiqlang</AlertDialogTitle>
            <AlertDialogDescription>
              {confirm?.kind === "source" ? (
                <>
                  <span className="font-medium text-foreground">{confirm.key}</span> dataseti va unga tegishli barcha
                  yozuvlar o'chiriladi.
                </>
              ) : (
                <>
                  <span className="font-medium text-foreground">{confirm?.key}</span> sensor turi bo'yicha barcha
                  ma'lumotlar o'chiriladi.
                </>
              )}{" "}
              Bu amalni qaytarib bo'lmaydi.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={del.isPending}>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                del.mutate();
              }}
              disabled={del.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {del.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
              O'chirish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
