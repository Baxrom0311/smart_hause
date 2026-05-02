import { NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Database, Cpu, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

const items = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/data", label: "Ma'lumotlar", icon: Database },
  { to: "/training", label: "Model o'qitish", icon: Cpu },
  { to: "/analysis", label: "Tahlil", icon: Activity },
];

interface Props {
  onNavigate?: () => void;
}

export function AppSidebar({ onNavigate }: Props) {
  const location = useLocation();
  return (
    <aside className="h-full w-full bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="px-4 pt-5 pb-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-md gradient-clay flex items-center justify-center shadow-sm">
            <Activity className="h-5 w-5 text-primary-foreground" strokeWidth={2.4} />
          </div>
          <div className="leading-tight">
            <div className="font-display font-semibold text-[15px] text-sidebar-foreground">
              Smart Home AI
            </div>
            <div className="text-[11px] uppercase text-muted-foreground">
              Monitoring
            </div>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 px-2.5">
        <nav className="flex flex-col gap-1 py-2">
          {items.map((it) => {
            const active = it.to === "/" ? location.pathname === "/" : location.pathname.startsWith(it.to);
            const Icon = it.icon;
            return (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.to === "/"}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
                  "text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent",
                  active && "bg-sidebar-accent text-sidebar-accent-foreground font-medium shadow-sm"
                )}
              >
                <Icon
                  className={cn(
                    "h-[18px] w-[18px] transition-colors",
                    active ? "text-primary" : "text-muted-foreground group-hover:text-sidebar-accent-foreground"
                  )}
                  strokeWidth={2}
                />
                <span>{it.label}</span>
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
              </NavLink>
            );
          })}
        </nav>
      </ScrollArea>

      <div className="px-4 py-3 border-t border-sidebar-border">
        <div className="text-[11px] text-muted-foreground leading-relaxed">LSTM Autoencoder</div>
      </div>
    </aside>
  );
}
