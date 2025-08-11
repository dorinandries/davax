import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Card } from 'react-bootstrap';
import { putere, fibo, factorial } from './api/api';

function App() {
  const [x, setX] = useState('');
  const [y, setY] = useState('');
  const [nFibo, setNFibo] = useState('');
  const [nFact, setNFact] = useState('');
  const [resultPutere, setResultPutere] = useState(null);
  const [resultFibo, setResultFibo] = useState(null);
  const [resultFact, setResultFact] = useState(null);

  const handlePutere = async () => {
    try {
      const res = await putere(Number(x), Number(y));
      setResultPutere(res);
    } catch (err) {
      console.error(err);
      alert('Eroare la calcul putere');
    }
  };

  const handleFibo = async () => {
    try {
      const res = await fibo(Number(nFibo));
      setResultFibo(res);
    } catch (err) {
      console.error(err);
      alert('Eroare la calcul Fibonacci');
    }
  };

  const handleFactorial = async () => {
    try {
      const res = await factorial(Number(nFact));
      setResultFact(res);
    } catch (err) {
      console.error(err);
      alert('Eroare la calcul factorial');
    }
  };

  return (
    <Container className="py-5">
      <h1 className="text-center mb-5">Tema Python - Operatii Matematice</h1>
      <Row className="g-4">
        {/* Putere */}
        <Col md={4}>
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title className="text-primary">X la puterea Y</Card.Title>
              <Form.Group className="mb-3">
                <Form.Control
                  type="number"
                  placeholder="X"
                  min="0"
                  value={x}
                  onChange={e => setX(e.target.value)}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Control
                  type="number"
                  placeholder="Y"
                  min="0"
                  value={y}
                  onChange={e => setY(e.target.value)}
                />
              </Form.Group>
              <Button variant="primary" onClick={handlePutere} className="w-100">
                Calculeaza
              </Button>
              {resultPutere !== null && (
                <Card.Text className="mt-3">
                  <strong>Rezultat:</strong> {resultPutere}
                </Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Fibonacci */}
        <Col md={4}>
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title className="text-success">Fibonacci</Card.Title>
              <Form.Group className="mb-3">
                <Form.Control
                  type="number"
                  placeholder="N"
                  min="0"
                  value={nFibo}
                  onChange={e => setNFibo(e.target.value)}
                />
              </Form.Group>
              <Button variant="success" onClick={handleFibo} className="w-100">
                Calculeaza
              </Button>
              {resultFibo !== null && (
                <Card.Text className="mt-3">
                  <strong>Rezultat:</strong> {resultFibo}
                </Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Factorial */}
        <Col md={4}>
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title className="text-danger">N Factorial</Card.Title>
              <Form.Group className="mb-3">
                <Form.Control
                  type="number"
                  placeholder="N"
                  min="0"
                  value={nFact}
                  onChange={e => setNFact(e.target.value)}
                />
              </Form.Group>
              <Button variant="danger" onClick={handleFactorial} className="w-100">
                Calculeaza
              </Button>
              {resultFact !== null && (
                <Card.Text className="mt-3">
                  <strong>Rezultat:</strong> {resultFact}
                </Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default App;
