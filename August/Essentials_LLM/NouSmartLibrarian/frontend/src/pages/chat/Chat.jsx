import React, { useState, useEffect } from "react";
import "../../styles/components/_chat.scss";
import { useAuth } from "../../context/AuthProvider";
import MessageBubble from "../../components/message/MessageBubble";
import { Button, Container, Paper, Typography } from "@mui/material";
import ChatInput from "../../components/chat/ChatInput";
import api from "../../api/api";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [blocked, setBlocked] = useState(false);
  const [anonMsg, setAnonMsg] = useState("");
  const { user } = useAuth();
  const fetchAnonStatus = async () => {
    if (!user) {
      try {
        const { data } = await api.get("/chat/anon-status");
        setAnonMsg(data.message);
      } catch (e) {
        setAnonMsg("");
      }
    }
  };
  useEffect(() => {
    fetchAnonStatus();
  }, [user]);

  const send = async (text) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    try {
      const { data } = await api.post("/chat/recommend", { query: text });
      if (data.status === "blocked") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.message },
        ]);
        return;
      }
      if (data.status === "forbidden") {
        setBlocked(true);
        setAnonMsg(data.message || "");
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.message },
        ]);
        return;
      }
      // Dacă e neautentificat și există mesaj informativ, îl afișăm
      if (!user && data.message && data.status !== "success") {
        setAnonMsg(data.message);
      } else if (!user && data.message && data.status === "success") {
        // actualizeaza mesajul dacă totul e ok
        fetchAnonStatus();
      }
      if (data.status !== "success") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.message },
        ]);
        return;
      }
      const full = data.summary
        ? `${data.message}\n\nRezumat detaliat:\n${data.summary}`
        : data.message;
      setMessages((prev) => [...prev, { role: "assistant", content: full }]);
    } catch (e) {
      console.error("chat error", e);
      const msg =
        e?.response?.data?.detail ||
        e?.message ||
        "Eroare de rețea sau server.";
      setMessages((prev) => [...prev, { role: "assistant", content: msg }]);
    }
  };

  // TTS (frontend only)
  const speak = (text) => {
    if (!("speechSynthesis" in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utter);
  };

  return (
    <Container maxWidth="lg" className="chat-container">
      <Paper className="chat-card">
        <Typography variant="h5">Chatbot recomandări cărți</Typography>
        {!user && anonMsg && (
          <Typography variant="body2" sx={{ mb: 1 }} color="warning.main">
            {anonMsg}
          </Typography>
        )}
        <div className="messages">
          {messages.map((m, i) => (
            <MessageBubble
              key={i}
              role={m.role}
              content={m.content}
              onSpeak={() => speak(m.content)}
            />
          ))}
        </div>
        <ChatInput onSend={send} sttEnabled={!!user} />
        {blocked && (
          <Button href="/register" variant="outlined" sx={{ mt: 1 }}>
            Creează cont
          </Button>
        )}
      </Paper>
    </Container>
  );
}
