import React, { useState } from "react";
import {
  Container,
  TextField,
  Button,
  Paper,
  Typography,
  Grid,
} from "@mui/material";
import api from "../../api/api";
import { useNavigate } from "react-router-dom";
import "../../styles/components/_forms.scss";

export default function Register() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [code, setCode] = useState("");
  const [verified, setVerified] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [error, setError] = useState("");

  const sendCode = async () => {
    setError("");
    try {
      await api.post(`/auth/send-otp?email=${encodeURIComponent(email)}`);
      setCodeSent(true);
    } catch (e) {
      setError(e?.response?.data?.detail || "Nu s-a putut trimite codul");
    }
  };

  const verifyCode = async () => {
    setError("");
    try {
      await api.post("/auth/verify-otp", null, { params: { email, code } });
      setVerified(true);
    } catch (e) {
      setError(e?.response?.data?.detail || "Cod invalid");
    }
  };

  const validatePassword = (pwd) => {
    // minim 8 caractere, o literă mare, o cifră, un caracter special
    const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]).{8,}$/;
    return regex.test(pwd);
  };

  const onRegister = async (e) => {
    e.preventDefault();
    setError("");
    if (!validatePassword(password)) {
      setError("Parola trebuie să aibă minim 8 caractere, o literă mare, o cifră și un caracter special.");
      return;
    }
    try {
      await api.post("/auth/register", {
        email,
        username,
        password,
        first_name: first,
        last_name: last,
      });
      nav("/login");
    } catch (e) {
      setError(e?.response?.data?.detail || "Înregistrare eșuată");
    }
  };

  return (
    <Container maxWidth="sm" className="form-container">
      <Paper className="form-card">
        <Typography variant="h5">Creează cont</Typography>

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="Email"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={verified}
            />
          </Grid>
          {!verified && (
            <Grid item xs={12}>
              {!codeSent ? (
                <Button variant="outlined" onClick={sendCode}>
                  Send code
                </Button>
              ) : (
                <>
                  <TextField
                    label="Introduce codul"
                    fullWidth
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                  <Button
                    variant="contained"
                    onClick={verifyCode}
                    sx={{ mt: 1 }}
                  >
                    Verifică
                  </Button>
                </>
              )}
            </Grid>
          )}

          {verified && (
            <>
              <Grid item xs={12}>
                <TextField
                  label="Username"
                  fullWidth
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Parolă"
                  type="password"
                  fullWidth
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  helperText="Minim 8 caractere, o literă mare, o cifră și un caracter special."
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Prenume"
                  fullWidth
                  value={first}
                  onChange={(e) => setFirst(e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Nume"
                  fullWidth
                  value={last}
                  onChange={(e) => setLast(e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <Button fullWidth variant="contained" onClick={onRegister}>
                  Creează cont
                </Button>
              </Grid>
            </>
          )}
        </Grid>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </Paper>
    </Container>
  );
}
