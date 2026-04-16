import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { AssignmentBanner } from "./components/AssignmentBanner.jsx";
import { NotesLayout } from "./layout/NotesLayout.jsx";
import { DocWorkspace } from "./pages/DocWorkspace.jsx";
import { LinkDoc } from "./pages/LinkDoc.jsx";
import { Login } from "./pages/Login.jsx";
import { NotesHome } from "./pages/NotesHome.jsx";

export function App() {
  const { token } = useAuth();
  return (
    <>
      <AssignmentBanner />
      <div className="app-routes-grow">
      <Routes>
        <Route path="/link/:token" element={<LinkDoc />} />
        <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
        <Route
          path="/"
          element={token ? <NotesLayout /> : <Navigate to="/login" replace />}
        >
          <Route index element={<NotesHome />} />
          <Route path="doc/:id" element={<DocWorkspace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </div>
    </>
  );
}
