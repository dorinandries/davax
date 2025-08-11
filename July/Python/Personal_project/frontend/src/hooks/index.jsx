import { useContext } from "react";
import AuthContext from "../context/authentication";

export const useAuthProvider = () => {
  return useContext(AuthContext);
};
