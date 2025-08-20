import React, { useState } from "react";
import { Container, TextField, Button, Paper, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthProvider";
import "../../styles/components/_forms.scss";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(identifier, password);
      nav("/chat");
    } catch (e) {
      setError("Autentificare eșuată");
    }
  };

  return (
    <Container maxWidth="sm" className="form-container">
      <Paper className="form-card">
        <Typography variant="h5">Login</Typography>
        <form onSubmit={onSubmit}>
          <TextField
            label="Email sau Username"
            fullWidth
            margin="normal"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
          <TextField
            label="Parola"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <Typography color="error">{error}</Typography>}
          <Button type="submit" variant="contained" fullWidth>
            Intră
          </Button>
          <Button variant="text" onClick={() => nav("/reset-password")}>
            Ai uitat parola?
          </Button>
        </form>
      </Paper>
    </Container>
  );
}
