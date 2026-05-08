import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, CalendarDays, ScrollText, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/",         icon: LayoutDashboard, label: "Dashboard"   },
  { to: "/accounts", icon: Users,           label: "Nick Manager" },
  { to: "/schedule", icon: CalendarDays,    label: "Lịch 30 ngày" },
  { to: "/logs",     icon: ScrollText,      label: "Logs"         },
];

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-white border-r border-slate-200 flex flex-col z-40">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-5 border-b border-slate-100">
        <div className="w-8 h-8 bg-primary rounded-xl flex items-center justify-center shadow-sm">
          <Zap className="w-4 h-4 text-white fill-white" />
        </div>
        <div className="flex items-baseline gap-0.5">
          <span className="text-base font-black text-slate-900 tracking-tight">Badminton</span>
          <span className="text-base font-black text-primary tracking-tight ml-0.5">Go</span>
        </div>
      </div>

      {/* Sub-label */}
      <div className="px-5 pt-4 pb-2">
        <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Nick Farmer</p>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 flex flex-col gap-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            )}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-slate-100">
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Tự động nuôi nick<br />theo lịch 30 ngày
        </p>
      </div>
    </aside>
  );
}
