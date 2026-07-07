import { Toast } from "@heroui/react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { AgreementsList } from "./pages/AgreementsList";
import { AgreementDetail } from "./pages/AgreementDetail";
import { HostsList } from "./pages/HostsList";
import { HostDetail } from "./pages/HostDetail";
import { CatalogProducts } from "./pages/CatalogProducts";
import { Reports } from "./pages/Reports";
import { Settings } from "./pages/Settings";
import { ThemeProvider } from "./components/ThemeProvider";

export function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Toast.Provider placement="bottom end" />
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agreements" element={<AgreementsList />} />
            <Route path="/agreements/:id" element={<AgreementDetail />} />
            <Route path="/hosts" element={<HostsList />} />
            <Route path="/hosts/:id" element={<HostDetail />} />
            <Route path="/products" element={<CatalogProducts />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}
