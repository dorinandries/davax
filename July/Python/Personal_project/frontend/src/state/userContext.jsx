// React context pentru date utilizator
import React, { createContext, useState } from "react";

export const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [userContext, setUserContext] = useState({
    role: "",
    experience: "",
    seniority: ""
  });
  return (
    <UserContext.Provider value={{ userContext, setUserContext }}>
      {children}
    </UserContext.Provider>
  );
}
