import React from "react";
import { AppBar, Toolbar, Button, Typography } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthProvider";
import "../../styles/components/_navbar.scss";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <AppBar position="fixed" className="navbar">
      <Toolbar className="toolbar">
        <Typography
          variant="h6"
          className="brand"
          onClick={() => navigate("/")}
        >
          Smart Librarian
        </Typography>
        <div>
          {user ? (
            <>
              <Button color="inherit" component={Link} to="/profile">
                Profil
              </Button>
              <Button color="inherit" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button color="inherit" component={Link} to="/login">
                Login
              </Button>
              <Button color="inherit" component={Link} to="/register">
                Register
              </Button>
            </>
          )}
        </div>
      </Toolbar>
    </AppBar>
  );
}
