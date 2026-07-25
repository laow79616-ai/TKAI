import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from "react";
import { NavLink } from "react-router-dom";

export function Card({ children }: PropsWithChildren) { return <section className="card">{children}</section>; }
export function Loading() { return <p role="status">Loading…</p>; }
export function Table({ children }: PropsWithChildren) { return <table>{children}</table>; }
export function Header({ onLogout }: { onLogout(): void }) { return <header><strong>TKAI Marketplace Server</strong><button onClick={onLogout}>Logout</button></header>; }
export function Sidebar({ pages }: { pages: readonly string[] }) { return <aside><strong>Dashboard</strong>{pages.map((page) => <NavLink key={page} to={`/${page}`}>{page}</NavLink>)}</aside>; }
export function SearchBar({ value, onChange, onSubmit }: { value: string; onChange(value: string): void; onSubmit(): void }) { return <form onSubmit={(event) => { event.preventDefault(); onSubmit(); }}><input value={value} onChange={(event) => onChange(event.target.value)} placeholder="Search" /><button type="submit">Search</button></form>; }

interface BoundaryState { error: Error | null; }
export class ErrorBoundary extends Component<PropsWithChildren, BoundaryState> {
  state: BoundaryState = { error: null };
  static getDerivedStateFromError(error: Error): BoundaryState { return { error }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) {}
  render(): ReactNode { return this.state.error ? <p role="alert">{this.state.error.message}</p> : this.props.children; }
}
