import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Explore from "./pages/Explore";
import DocumentView from "./pages/DocumentView";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const qc = new QueryClient();
export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <nav style={{ padding: 12, borderBottom: "1px solid #ddd" }}>
          <Link to="/">Newmark ETL</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Explore />} />
          <Route path="/doc/:id" element={<DocumentView />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
