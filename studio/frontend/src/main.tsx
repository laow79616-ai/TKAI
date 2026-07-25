import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { App } from "./App";
import { studioPages } from "./pages";

const Page = ({ name }: { name: string }) => <h1>{name}</h1>;
createRoot(document.getElementById("root")!).render(<StrictMode><BrowserRouter><Routes><Route path="/" element={<App />}>{studioPages.map((page) => <Route key={page} path={page} element={<Page name={page} />} />)}</Route></Routes></BrowserRouter></StrictMode>);
