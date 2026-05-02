import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionCardProps {
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function SectionCard({ title, description, actions, children, className, bodyClassName }: SectionCardProps) {
  return (
    <section className={cn("surface-card overflow-hidden", className)}>
      {(title || actions) && (
        <header className="flex flex-wrap items-center gap-3 px-4 sm:px-5 py-3 border-b border-border/70">
          <div className="min-w-0 flex-1">
            {title && <h2 className="font-display text-sm sm:text-base font-semibold leading-tight">{title}</h2>}
            {description && (
              <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
        </header>
      )}
      <div className={cn("p-4 sm:p-5", bodyClassName)}>{children}</div>
    </section>
  );
}
