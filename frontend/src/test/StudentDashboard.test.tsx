import { render, screen, waitFor } from "@testing-library/react";
import StudentDashboard  from "../pages/operator/Dashboard";
import { vi } from "vitest";
declare const global: any;

global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ active: true, zone: "A1" }),
}) as any;

test("shows active parking session", async () => {
  render(<StudentDashboard />);

  await waitFor(() =>
    expect(screen.getByText(/active session/i)).toBeInTheDocument()
  );
  expect(screen.getByText(/zone: A1/i)).toBeInTheDocument();
});