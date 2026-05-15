// This file defines the AuthContext and AuthProvider components for managing authentication state in the React application.

// Import necessary hooks and functions from React
import { createContext, useContext, useState } from "react";

// Define the shape of the authentication context
interface AuthContextType {
  token: string | null;
  role: string | null;
  login: (token: string, role: string) => void;
  logout: () => void;
}

// Create the authentication context with a default value of null
const AuthContext = createContext<AuthContextType | null>(null);

// Define the AuthProvider component that will wrap the application and provide authentication state
export const AuthProvider = ({ children }: any) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [role, setRole] = useState(localStorage.getItem("role"));

// Login function to update the authentication state and store the token and role in localStorage
  const login = (token: string, role: string) => {
    setToken(token);
    setRole(role);
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
  };

// Logout function to clear the authentication state and remove the token and role from localStorage
  const logout = () => {
    setToken(null);
    setRole(null);
    localStorage.removeItem("token");
    localStorage.removeItem("role");
  };
  
  return (
    <AuthContext.Provider value={{ token, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext)!;
