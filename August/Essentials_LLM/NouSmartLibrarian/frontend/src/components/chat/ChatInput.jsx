import React, { useState, useRef } from "react";
import { TextField, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import MicIcon from "@mui/icons-material/Mic";

export default function ChatInput({ onSend, sttEnabled }) {
  const [text, setText] = useState("");
  const recRef = useRef(null);

  const startSTT = () => {
    if (!sttEnabled) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = "ro-RO";
    rec.interimResults = false;
    rec.onresult = (e) => {
      const t = e.results[0][0].transcript;
      setText(t);
    };
    rec.start();
    recRef.current = rec;
  };

  const submit = (e) => {
    e?.preventDefault();
    onSend(text);
    setText("");
  };

  return (
    <form onSubmit={submit} className="chat-input">
      <TextField
        fullWidth
        placeholder="Ex: Vreau o carte despre prietenie și magie"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {sttEnabled && (
        <IconButton onClick={startSTT} aria-label="voice input">
          <MicIcon />
        </IconButton>
      )}
      <IconButton type="submit" aria-label="send">
        <SendIcon />
      </IconButton>
    </form>
  );
}
