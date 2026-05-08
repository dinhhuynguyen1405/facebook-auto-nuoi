import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { DashboardPage } from "@/pages/dashboard";
import { AccountsPage } from "@/pages/accounts";
import { SchedulePage } from "@/pages/schedule";
import { LogsPage } from "@/pages/logs";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface-2">
        <Sidebar />
        <main className="flex-1 flex flex-col overflow-hidden ml-56">
          <Routes>
            <Route path="/"         element={<DashboardPage />} />
            <Route path="/accounts" element={<AccountsPage />}  />
            <Route path="/schedule" element={<SchedulePage />}  />
            <Route path="/logs"     element={<LogsPage />}      />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
