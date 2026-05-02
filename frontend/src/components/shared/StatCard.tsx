import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  tone?: "default" | "primary" | "teal" | "sage" | "amber" | "danger";
  loading?: boolean;
}

const toneStyles: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "bg-muted text-muted-foreground",
  primary: "bg-primary-soft text-primary",
  teal: "bg-secondary text-secondary-foreground",
  sage: "bg-accent text-accent-foreground",
  amber: "bg-amber/15 text-amber-foreground",
  danger: "bg-destructive-soft text-destructive",
};

export function StatCard({ label, value, hint, icon, tone = "default", loading }: StatCardProps) {
  return (
    <div className="surface-card surface-hover p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-[11px] font-medium uppercase tracking-normal text-muted-foreground">
          {label}
        </div>
        {icon && (
          <div className={cn("h-8 w-8 rounded-md flex items-center justify-center shrink-0", toneStyles[tone])}>
            {icon}
          </div>
        )}
      </div>
      <div className="mt-2 font-display text-xl sm:text-2xl font-semibold tabular-nums">
        {loading ? <Skeleton className="h-7 w-20" /> : value}
      </div>
      {hint && <div className="mt-1 text-xs text-muted-foreground truncate">{hint}</div>}
    </div>
  );
}
