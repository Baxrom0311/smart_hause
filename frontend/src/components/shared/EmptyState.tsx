import type { ReactNode } from "react";
import { Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, description, icon, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center py-8 px-4", className)}>
      <div className="h-10 w-10 rounded-md bg-muted text-muted-foreground flex items-center justify-center mb-3">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <div className="font-display font-semibold text-sm">{title}</div>
      {description && <p className="mt-1 text-sm text-muted-foreground max-w-md">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
