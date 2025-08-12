import React, { useState } from "react";
import { useAuth } from "../../context";
import "./navbar.css"; // Make sure to import the CSS

const Navbar = ({ onLoginClick, onLogout }) => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    if (onLogout) onLogout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">Math Microservice</div>
      <div className="navbar-actions">
        {user ? (
          <div
            className="navbar-user"
            onMouseEnter={() => setDropdownOpen(true)}
            onMouseLeave={() => setDropdownOpen(false)}
          >
            <span className="navbar-username">{user.username}</span>
            {dropdownOpen && (
              <div className="navbar-dropdown">
                <button className="navbar-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <button className="navbar-btn" onClick={onLoginClick}>
            Login
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
