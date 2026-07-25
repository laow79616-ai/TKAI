import type { PropsWithChildren } from "react";

export function Card({ children }: PropsWithChildren) { return <section className="card">{children}</section>; }
export function Status({ value }: { value: string }) { return <span className="status">{value}</span>; }
export function Loading() { return <p>Loading…</p>; }
export function Notification({ message }: { message: string }) { return <aside role="status">{message}</aside>; }
export function Table({ children }: PropsWithChildren) { return <table>{children}</table>; }
export function Dialog({ children }: PropsWithChildren) { return <dialog open>{children}</dialog>; }
export function Form({ children }: PropsWithChildren) { return <form>{children}</form>; }
