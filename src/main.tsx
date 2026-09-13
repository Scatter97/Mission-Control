import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter } from "react-router-dom";

import { App } from "./app/App";
import { BackendProvider } from "./backend/BackendProvider";
import { UiPreferencesProvider } from "./app/preferences/UiPreferencesProvider";
import { ThemeProvider } from "./app/theme/ThemeProvider";

import "./app/theme/tokens.css";
import "./styles/globals.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: 1
    }
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BackendProvider>
        <ThemeProvider>
          <UiPreferencesProvider>
            <HashRouter>
              <App />
            </HashRouter>
          </UiPreferencesProvider>
        </ThemeProvider>
      </BackendProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
