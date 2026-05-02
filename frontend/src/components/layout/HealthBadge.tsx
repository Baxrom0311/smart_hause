import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";
import { Wifi, WifiOff, Loader2 } from "lucide-react";

export function HealthBadge() {
  const { data, isLoading, isError } = useHealth();
  const ok = !!data && !isError;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium",
        ok && "border-sage/30 bg-accent text-accent-foreground",
        !ok && !isLoading && "border-destructive/30 bg-destructive-soft text-destructive",
        isLoading && "border-border bg-muted text-muted-foreground"
      )}
      title={ok ? "Backend online" : "Backend offline"}
    >
      {isLoading ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : ok ? (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full rounded-full bg-sage opacity-60 animate-ping" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-sage" />
        </span>
      ) : (
        <WifiOff className="h-3.5 w-3.5" />
      )}
      <span className="hidden sm:inline">{ok ? "Online" : isLoading ? "..." : "Offline"}</span>
      {ok && <Wifi className="h-3.5 w-3.5 hidden md:inline opacity-60" />}
    </div>
  );
}
