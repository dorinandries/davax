import React from "react";
import { Paper, Button } from "@mui/material";
import '../../styles/components/_message.scss';

export default function MessageBubble({ role, content, onSpeak }) {
  return (
      <div className={`message-bubble ${role}`}>
      <div className="bubble-paper">
        <pre>{content}</pre>
        <div className="bubble-actions">
          <Button size="small" onClick={onSpeak}>
            Ascultă
          </Button>
        </div>
      </div>
    </div>
    );
}
