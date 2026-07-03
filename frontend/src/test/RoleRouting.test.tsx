import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { AuthProvider } from "../auth/AuthContext";

function renderWithAuth(role: "PARKER" | "OPERATOR" | "ENFORCEMENT") {
  localStorage.setItem("auth_role", role);
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>
    </AuthProvider>
  );
}

afterEach(() => {
  localStorage.clear();
});

test("parker sees student dashboard", () => {
  renderWithAuth("PARKER");
  expect(screen.getByText(/student dashboard/i)).toBeInTheDocument();
});
