// main.tsx — React entry, mounts the router.
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/600.css";
import "@fontsource/geist-mono/400.css";
import "@fontsource/geist-mono/500.css";
import "./index.css";

// Convenience: accept ?token=…&project=… once and persist to localStorage,
// then clean them out of the URL. Lets the demo seeder hand you a ready link.
const params = new URLSearchParams(window.location.search);
const urlToken = params.get("token");
const urlProject = params.get("project");
if (urlToken) localStorage.setItem("axiom_token", urlToken);
if (urlProject) localStorage.setItem("axiom_project", urlProject);
if (urlToken || urlProject) {
  window.history.replaceState({}, "", window.location.pathname);
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
