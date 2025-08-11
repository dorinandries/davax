// src/App.jsx
import React, { useEffect, useState } from "react";
import Scenes from "./components/environment/scene";
import { UserProvider } from "./state/userContext";
import UserForm from "./components/environment/modals/userForm";
import Login from "./layout/authentication";
import MenuModal from "./components/environment/modals/menu/menuModal";
import "./App.css";
import { useAuthProvider } from "./hooks";

export default function App() {
  const { user, token, setToken, logout} = useAuthProvider();
  const [showUserForm, setShowUserForm] = useState(false);
  const [showMenuModal, setShowMenuModal] = useState(false);

  // PROXIMITY + CHAT MODAL STATE
  const [nearAvatar, setNearAvatar] = useState(null);

  useEffect(() => {
    if (user) {
      // dacă lipsesc oricare dintre câmpuri, afișăm form:
      setShowUserForm(!user.role || !user.seniority || !user.experience);
    } else {
      setShowUserForm(false);
    }
  }, [user]);

  const handleLogin = (token) => {
    setToken(token);
  };

  const handleLogout = () => {
    logout()
    setShowMenuModal(false);
    setShowUserForm(false);
  };

  // Called by Scenes → Experience when camera enters/exits an avatar’s radius
  const handleProximityChange = (avatarName) => {
    setNearAvatar(avatarName);
  };

  return (
    <UserProvider>
      <div className="app-root">
        {!token && <Login onLogin={handleLogin} />}

        {token && (
          <>
            <div className="app-container">
              <Scenes
                controlsEnabled={!showUserForm && !showMenuModal}
                onProximity={handleProximityChange}
                nearAvatar={nearAvatar}
              />
            </div>

            <button
              className="menu-button"
              onClick={() => setShowMenuModal(true)}
            >
              ☰ Menu
            </button>

            {showUserForm && (
              <UserForm onClose={() => setShowUserForm(false)} />
            )}

            {showMenuModal && (
              <MenuModal
                onEditProfile={() => {
                  setShowUserForm(true);
                  setShowMenuModal(false);
                }}
                onLogout={handleLogout}
                onClose={() => setShowMenuModal(false)}
              />
            )}
          </>
        )}
      </div>
    </UserProvider>
  );
}
