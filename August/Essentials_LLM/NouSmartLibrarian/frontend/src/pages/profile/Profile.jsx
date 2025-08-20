import React, { useState } from "react";
import {
  Container,
  Paper,
  Typography,
  Chip,
  TextField,
  Button,
} from "@mui/material";
import api from "../../api/api";

export default function Profile() {
  const [genres, setGenres] = useState([]);
  const [input, setInput] = useState("");
  const add = () => {
    if (input.trim()) {
      setGenres((g) => [...new Set([...g, input.trim()])]);
      setInput("");
    }
  };
  const save = async () => {
    await api.post("/auth/preferences", { genres });
  };
  return (
    <Container maxWidth="sm" className="form-container">
      <Paper className="form-card">
        <Typography variant="h5">Preferințe</Typography>
        <div
          style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "8px 0" }}
        >
          {genres.map((g, i) => (
            <Chip
              key={i}
              label={g}
              onDelete={() => setGenres(genres.filter((x) => x !== g))}
            />
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <TextField
            label="Gen nou"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button variant="outlined" onClick={add}>
            Adaugă
          </Button>
          <Button variant="contained" onClick={save}>
            Salvează
          </Button>
        </div>
      </Paper>
    </Container>
  );
}
