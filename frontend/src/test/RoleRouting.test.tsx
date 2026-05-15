import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { AuthProvider } from "../context/AuthContext";

function renderWithAuth(role: "PARKER" | "OPERATOR" | "ENFORCEMENT") {
  return render(
    <AuthProvider initialValue={{ role, token: "fake", isAuthenticated: true }}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>
    </AuthProvider>
  );
}

test("parker sees student dashboard", () => {
  renderWithAuth("PARKER");
  expect(screen.getByText(/student dashboard/i)).toBeInTheDocument();
});