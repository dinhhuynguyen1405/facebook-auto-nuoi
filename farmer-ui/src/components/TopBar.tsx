import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface TopBarProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  refreshing?: boolean;
  action?: React.ReactNode;
}

export function TopBar({ title, subtitle, onRefresh, refreshing, action }: TopBarProps) {
  return (
    <div className="h-14 bg-white border-b border-slate-200 px-6 flex items-center gap-4 sticky top-0 z-30">
      <div className="flex-1 min-w-0">
        <h1 className="text-base font-bold text-slate-900 truncate">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 truncate">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        {action}
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-slate-100 transition-colors text-slate-500"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
          </button>
        )}
      </div>
    </div>
  );
}
