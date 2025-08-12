import React, { useState } from "react";
import { Card as RBCard, Form, Button } from "react-bootstrap";
import { useAuth } from "../../context";
import { FaLock } from "react-icons/fa";
import "./Card.css";

const Card = ({
  title,
  colorClass,
  xLabel,
  yLabel,
  x,
  setX,
  y,
  setY,
  calculate,
  result,
  require_auth = false,
  resultLabel = "Rezultat",
}) => {
  const { user } = useAuth();
  const [localX, setLocalX] = useState(x || "");
  const [localY, setLocalY] = useState(y || "");

  // For cards with only one input (like Fibonacci, Factorial)
  const isSingleInput = typeof setY !== "function";

  const handleCalculate = () => {
    if (isSingleInput) {
      calculate(localX);
    } else {
      calculate(localX, localY);
    }
  };

  // Keep parent state in sync if provided
  const handleXChange = (e) => {
    setLocalX(e.target.value);
    if (setX) setX(e.target.value);
  };
  const handleYChange = (e) => {
    setLocalY(e.target.value);
    if (setY) setY(e.target.value);
  };

  const locked = require_auth && !user;

  return (
    <div className="custom-card-wrapper">
      <RBCard className={`h-100 shadow-sm`}>
        <RBCard.Body>
          <RBCard.Title className={colorClass}>{title}</RBCard.Title>
          <Form.Group className="mb-3">
            <Form.Control
              type="number"
              placeholder={xLabel}
              min="0"
              value={localX}
              onChange={handleXChange}
              disabled={locked}
            />
          </Form.Group>
          {!isSingleInput && (
            <Form.Group className="mb-3">
              <Form.Control
                type="number"
                placeholder={yLabel}
                min="0"
                value={localY}
                onChange={handleYChange}
                disabled={locked}
              />
            </Form.Group>
          )}
          <Button
            variant={colorClass.replace("text-", "")}
            onClick={handleCalculate}
            className="w-100"
            disabled={locked}
          >
            Calculeaza
          </Button>
          {result !== null && (
            <RBCard.Text className="mt-3">
              <strong>{resultLabel}:</strong> {result}
            </RBCard.Text>
          )}
        </RBCard.Body>
        {locked && (
          <div className="card-auth-overlay">
            <FaLock size={40} color="#235390" />
            <div className="card-auth-text">
              Autentificare necesară pentru această operație.
            </div>
          </div>
        )}
      </RBCard>
    </div>
  );
};

export default Card;
