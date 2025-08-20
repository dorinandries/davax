import React, { useState } from "react";
import {
  Container,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Alert,
} from "@mui/material";
import api from "../../api/api";
import "../../styles/components/_forms.scss";

const isStrong = (p) =>
  p.length >= 8 && /[A-Z]/.test(p) && /\d/.test(p) && /[^A-Za-z0-9]/.test(p);

export default function ResetPassword() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [pw1, setPw1] = useState("");
  const [pw2, setPw2] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  const sendCode = async () => {
    setError("");
    setOk("");
    try {
      await api.post(`/auth/reset/send-otp?email=${encodeURIComponent(email)}`);
      setOk("Codul a fost trimis dacă adresa există.");
      setStep(2);
    } catch (e) {
      setError(e?.response?.data?.detail || "Nu s-a putut trimite codul");
    }
  };

  const verifyCode = async () => {
    setError("");
    setOk("");
    try {
      await api.post("/auth/reset/verify", null, { params: { email, code } });
      setStep(3);
    } catch (e) {
      setError(e?.response?.data?.detail || "Cod invalid");
    }
  };
  const complete = async () => {
    setError("");
    setOk("");
    if (pw1 !== pw2) {
      setError("Parolele nu corespund");
      return;
    }
    if (!isStrong(pw1)) {
      setError(
        "Parola trebuie să aibă min 8 caractere, o literă mare, o cifră și un caracter special."
      );
      return;
    }
    try {
      await api.post("/auth/reset/complete", {
        email,
        code,
        new_password: pw1,
      });
      setOk("Parola a fost resetată. Poți să te loghezi acum.");
      setStep(4);
    } catch (e) {
      setError(e?.response?.data?.detail || "Nu s-a putut reseta parola");
    }
  };

  return (
    <Container maxWidth="sm" className="form-container">
      <Paper className="form-card">
        <Typography variant="h5">Resetare parolă</Typography>
        {error && (
          <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
            {error}
          </Alert>
        )}
        {ok && (
          <Alert severity="success" sx={{ mt: 1, mb: 1 }}>
            {ok}
          </Alert>
        )}

        {step === 1 && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                label="Email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="contained" fullWidth onClick={sendCode}>
                Trimite cod
              </Button>
            </Grid>
          </Grid>
        )}

        {step === 2 && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                label="Codul primit"
                fullWidth
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="contained" fullWidth onClick={verifyCode}>
                Verifică
              </Button>
            </Grid>
          </Grid>
        )}

        {step === 3 && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                label="Parolă nouă"
                type="password"
                fullWidth
                value={pw1}
                onChange={(e) => setPw1(e.target.value)}
                helperText="Min 8 caractere, 1 literă mare, 1 cifră, 1 caracter special"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Confirmă parola nouă"
                type="password"
                fullWidth
                value={pw2}
                onChange={(e) => setPw2(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="contained" fullWidth onClick={complete}>
                Resetează parola
              </Button>
            </Grid>
          </Grid>
        )}

        {step === 4 && (
          <Button variant="outlined" href="/login">
            Mergi la login
          </Button>
        )}
      </Paper>
    </Container>
  );
}
