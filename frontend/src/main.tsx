import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/index.css";
import "@fontsource/poppins/300.css";
import "@fontsource/poppins/400.css";
import "@fontsource/poppins/500.css";
import "@fontsource/poppins/700.css";
import { ThemeProvider } from "@mui/material/styles";
import "react-toastify/dist/ReactToastify.css";
import theme from "./hooks/useTheme.ts";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { Provider } from "react-redux";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "./hooks/useReactQuery.ts";
import { store } from "./app/store.ts";
import { AuthProvider } from "./features/auth/components/index.ts";
import routes from "./app/routes.tsx";
import ToastBox from "./components/ui/ToastBox.tsx";

const router = createBrowserRouter(routes);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RouterProvider router={router} />
            <ToastBox />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>
  </StrictMode>,
);
