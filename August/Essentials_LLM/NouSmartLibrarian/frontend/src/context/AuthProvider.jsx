import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../api/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // useEffect(() => {
  //   api
  //     .get("/auth/me")
  //     .then(({ data }) => {
  //       setUser(data.user || null);
  //     })
  //     .finally(() => setLoading(false));
  // }, []);
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        // 1) încearcă să reînnoiești access token-ul pe baza refresh cookie-ului
        await api.post("/auth/refresh");
      } catch (e) {
        // e ok dacă refresh-ul nu există/expirat
      }
      try {
        // 2) întreabă cine sunt
        const { data } = await api.get("/auth/me");
        if (alive) setUser(data.user); // adaptat la structura răspunsului tău
      } catch (e) {
        if (alive) setUser(null);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);
  
  const login = async (identifier, password) => {
    await api.post("/auth/login", { identifier, password });
    const { data } = await api.get("/auth/me");
    setUser(data.user || null);
  };

  const logout = async () => {
    await api.post("/auth/logout");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
