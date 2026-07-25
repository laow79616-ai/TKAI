import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";
import { ErrorBoundary, Header, Sidebar } from "./components";
import { dashboardPages, DashboardHome, HealthPage, LoginPage, NotFoundPage, PackagesPage, PublishersPage, RegistryPage, SearchPage, StatisticsPage, VersionsPage } from "./pages";

function Shell() {
  const { token, logout } = useAuth(); const navigate = useNavigate();
  if (!token) return <Navigate to="/login" replace />;
  return <div className="dashboard-shell"><Sidebar pages={dashboardPages} /><main><Header onLogout={() => { logout().finally(() => navigate("/login")); }} /><ErrorBoundary><Outlet /></ErrorBoundary></main></div>;
}

export function App() { return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<Shell />}><Route path="/dashboard" element={<DashboardHome />} /><Route path="/registry" element={<RegistryPage />} /><Route path="/publishers" element={<PublishersPage />} /><Route path="/packages" element={<PackagesPage />} /><Route path="/versions" element={<VersionsPage />} /><Route path="/search" element={<SearchPage />} /><Route path="/statistics" element={<StatisticsPage />} /><Route path="/health" element={<HealthPage />} /></Route><Route path="/" element={<Navigate to="/dashboard" replace />} /><Route path="*" element={<NotFoundPage />} /></Routes>; }
