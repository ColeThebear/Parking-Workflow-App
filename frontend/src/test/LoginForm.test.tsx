import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "../components/LoginForm";

test("submits email and password", async () => {
  const handleSubmit = vi.fn();
  render(<LoginForm onSubmit={handleSubmit} />);

  await userEvent.type(screen.getByLabelText(/email/i), "student@example.com");
  await userEvent.type(screen.getByLabelText(/password/i), "password123");
  await userEvent.click(screen.getByRole("button", { name: /login/i }));

  expect(handleSubmit).toHaveBeenCalledWith({
    email: "student@example.com",
    password: "password123",
  });
});
