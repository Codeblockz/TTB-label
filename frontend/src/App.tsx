import { BrowserRouter, Routes, Route } from "react-router";
import Layout from "./components/layout/Layout";
import UploadPage from "./pages/UploadPage";
import BatchUploadPage from "./pages/BatchUploadPage";
import HistoryPage from "./pages/HistoryPage";
import ResultPage from "./pages/ResultPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<UploadPage />} />
          <Route path="batch" element={<BatchUploadPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="results/:id" element={<ResultPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
