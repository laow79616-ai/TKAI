import { NavLink, Outlet } from "react-router-dom";
import { studioPages } from "./pages";
import { Card } from "./components";

export function App() {
  return <div className="studio-shell"><aside><strong>TKAI Studio</strong>{studioPages.map((page) => <NavLink key={page} to={`/${page}`}>{page}</NavLink>)}</aside><main><header>Studio</header><Card><Outlet /></Card></main></div>;
}
