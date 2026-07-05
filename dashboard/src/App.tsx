// App.tsx — routes wrapped in the shared Layout shell.
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import GraphExplorer from "./pages/GraphExplorer";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/graph" element={<GraphExplorer />} />
      </Routes>
    </Layout>
  );
}
