import React, { useState } from "react";
import { Container, Row, Col } from "react-bootstrap";
import { putere, fibo, factorial, prime } from "./api/api";
import Navbar from "./components/navbar";
import LoginModal from "./components/authentication/login";
import { useAuth } from "./context";
import Card from "./components/card";

function App() {
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [nFibo, setNFibo] = useState("");
  const [nFact, setNFact] = useState("");
  const [resultPutere, setResultPutere] = useState(null);
  const [resultFibo, setResultFibo] = useState(null);
  const [resultFact, setResultFact] = useState(null);
  const [nPrime, setNPrime] = useState("");
  const [resultPrime, setResultPrime] = useState(null);
  const [showLogin, setShowLogin] = useState(false);

  const { token } = useAuth();

  // Calculation handlers
  const handlePutere = async (xVal, yVal) => {
    try {
      const res = await putere(Number(xVal), Number(yVal));
      setResultPutere(res);
    } catch (err) {
      console.error(err);
      alert("Eroare la calcul putere");
    }
  };

  const handleFibo = async (n) => {
    try {
      const res = await fibo(Number(n));
      setResultFibo(res);
    } catch (err) {
      console.error(err);
      alert("Eroare la calcul Fibonacci");
    }
  };

  const handleFactorial = async (n) => {
    try {
      const res = await factorial(Number(n));
      setResultFact(res);
    } catch (err) {
      console.error(err);
      alert("Eroare la calcul factorial");
    }
  };

  const handlePrime = async (n) => {
    try {
      const res = await prime(Number(n), token);
      // Format the result for display
      if (typeof res === "object" && res !== null && "is_prime" in res) {
        setResultPrime(
          res.is_prime
            ? `${res.input.n} este prim`
            : `${res.input.n} nu este prim`
        );
      } else {
        setResultPrime(res);
      }
    } catch (err) {
      setResultPrime(err.response?.data?.detail || "Error checking prime");
    }
  };

  // Card configuration
  const cards = [
    {
      key: "putere",
      title: "X la puterea Y",
      colorClass: "text-primary",
      xLabel: "X",
      yLabel: "Y",
      x,
      setX,
      y,
      setY,
      calculate: handlePutere,
      result: resultPutere,
      require_auth: false,
      resultLabel: "Rezultat",
    },
    {
      key: "fibo",
      title: "Fibonacci",
      colorClass: "text-success",
      xLabel: "N",
      x: nFibo,
      setX: setNFibo,
      calculate: handleFibo,
      result: resultFibo,
      require_auth: false,
      resultLabel: "Rezultat",
    },
    {
      key: "factorial",
      title: "N Factorial",
      colorClass: "text-danger",
      xLabel: "N",
      x: nFact,
      setX: setNFact,
      calculate: handleFactorial,
      result: resultFact,
      require_auth: false,
      resultLabel: "Rezultat",
    },
    {
      key: "prime",
      title: "Numere Prime",
      colorClass: "text-warning",
      xLabel: "N",
      x: nPrime,
      setX: setNPrime,
      calculate: handlePrime,
      result: resultPrime,
      require_auth: true,
      resultLabel: "Rezultat",
    },
  ];

  const clearAll = () => {
    setX("");
    setY("");
    setNFibo("");
    setNFact("");
    setNPrime("");
    setResultPutere(null);
    setResultFibo(null);
    setResultFact(null);
    setResultPrime(null);
  };

  return (
    <>
      <Navbar onLoginClick={() => setShowLogin(true)} onLogout={clearAll} />
      <LoginModal show={showLogin} onClose={() => setShowLogin(false)} />
      <Container className="py-5">
        <h1 className="text-center mb-5">Tema Python - Operatii Matematice</h1>
        <Row className="g-4">
          {cards.map((card) => (
            <Col md={4} key={card.key}>
              <Card {...card} />
            </Col>
          ))}
        </Row>
      </Container>
    </>
  );
}

export default App;
