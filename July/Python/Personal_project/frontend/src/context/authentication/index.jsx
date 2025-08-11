// src/state/userContext.jsx
import React, { createContext, useEffect, useState } from "react";
import PropTypes from "prop-types";
import {jwtDecode} from "jwt-decode";

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(
        () => localStorage.getItem("token") || sessionStorage.getItem("token")
    );

    // useEffect(() => {
    //     if (token) {
    //         let decoded;
    //         try {
    //             decoded = jwtDecode(token);
    //         } catch {
    //             console.error("Token invalid, logout");
    //             logout();
    //             return;
    //         }
    //         loadUser(decoded.userID, token);
    //     } else {
    //         setUser(null);
    //     }
    // }, [token]);
    useEffect(() => {
        if (!token) {
            setUser(null);
            return;
        }
        let decoded;
        try {
            decoded = jwtDecode(token);
        } catch {
            logout();
            return;
        }
        loadUser(decoded.userID, token);
    }, [token]);

    const loadUser = async (userID = user?.userID, jwt = token) => {
        if (!userID || !jwt) return;
        try {
            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/user/${userID}`,
                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                        // Authorization: `Bearer ${jwt}`,
                    },
                }
            );
            if (res.ok) {
                const data = await res.json();
                setUser(data);
            } else {
                throw new Error("Cannot load the user profile");
            }
        } catch (err) {
            console.error("loadUser error:", err);
            logout();
        }
    };

    const logout = () => {
        sessionStorage.removeItem("token");
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                setToken,
                setUser,
                loadUser,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export default AuthContext;
