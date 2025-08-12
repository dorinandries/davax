import React, { useState } from "react";
import axios from "axios";
import { useAuth } from "../../context";
import { prime } from "../../api/api";

const PrimeCard = () => {
  const { token, user } = useAuth();
  const [n, setN] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleCheck = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    try {
      const res = await prime(n, token)
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || "Error checking prime");
    }
  };

  return (
    <div className="card">
      <h3>Prime Number Checker</h3>
      <form onSubmit={handleCheck}>
        <input
          type="number"
          min="2"
          placeholder="Enter n"
          value={n}
          onChange={e => setN(e.target.value)}
          required
        />
        <button type="submit">Check</button>
      </form>
      {result && (
        <div>
          {result.input.n} is {result.is_prime ? "prime" : "not prime"}
        </div>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default PrimeCard;