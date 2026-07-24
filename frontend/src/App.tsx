import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import LoginPage from "./pages/LoginPage";
import PlanningPage from "./pages/PlanningPage";
import ConstellationsPage from "./pages/ConstellationsPage";
import DemoReplayPage from "./pages/DemoReplayPage";
import Layout from "./components/Layout";

function App() {
  const { isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    // Check if user is still authenticated on app load
    fetchUser();
  }, [fetchUser]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {[
        { path: "/", element: <PlanningPage /> },
        { path: "/constellations", element: <ConstellationsPage /> },
        { path: "/demo/replay", element: <DemoReplayPage /> },
      ].map((route) => (
        <Route
          key={route.path}
          path={route.path}
          element={
            isAuthenticated ? (
              <Layout>{route.element}</Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      ))}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
