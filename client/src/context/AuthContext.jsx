import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { username, is_admin, token }
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("snip_auth");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("snip_auth");
      }
    }
    setLoading(false);
  }, []);

  function login(userData) {
    // userData: { access_token, is_admin, username }
    const authState = {
      token: userData.access_token,
      username: userData.username,
      is_admin: userData.is_admin,
    };
    setUser(authState);
    localStorage.setItem("snip_auth", JSON.stringify(authState));
  }

  function logout() {
    setUser(null);
    localStorage.removeItem("snip_auth");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
