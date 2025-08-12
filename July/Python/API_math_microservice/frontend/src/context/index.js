import React, { createContext, useContext, useEffect, useState } from "react";
import Cookies from "js-cookie";
import { getUserByID, login_user } from "../api/api";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // { username, id }
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    
    async function fetchData() {
      const jwt = Cookies.get("jwt_token");
      if (jwt) {
        console.log("useff", jwt);

        setToken(jwt);
        const payload = JSON.parse(atob(jwt.split(".")[1]));
        const get_user = await getUserByID(payload.sub);
        console.log("getuseR", get_user);

        setUser({
          id: get_user.data.id,
          email: get_user.data.email,
          username: get_user.data.username,
        });
      }
      setLoading(false);

    }
    fetchData();

  }, []);

  const login = async (identifier, password) => {
    try {
      const res = await login_user({
        identifier: identifier,
        password: password,
      });
      const { access_token } = res?.data;

      Cookies.set("jwt_token", access_token, {
        expires: 1,
        secure: true,
        sameSite: "strict",
      });
      const payload = JSON.parse(atob(access_token.split(".")[1]));
      const get_user = await getUserByID(payload.sub)
      setUser({
        id: get_user.data.id,
        email: get_user.data.email,
        username: get_user.data.username,
      });
      setToken(access_token);
      return { success: true };
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || "Login failed",
      };
    }
  };

  const logout = () => {
    Cookies.remove("jwt_token");
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
