# Python Projects Overview

This repository contains two distinct Python-based projects:

---

## 1. API Math Microservice

**Summary:**  
A simple microservice exposing mathematical operations (power, Fibonacci, factorial) via a REST API, built with FastAPI. It features persistent request logging using SQLite and includes both backend and frontend (React) components.

**Key Feature:**  
The backend caches results of previous computations in a SQLite database, so repeated requests for the same operation and input are served instantly from the database, improving efficiency.

---

## 2. AI Office Mentors – Virtual Assistant

**Summary:**  
An interactive web application simulating an office environment with three AI-powered virtual mentors (Senior .NET Developer, Senior Software Tester, Senior Data Engineer). Users can create a profile, approach mentors in a 3D scene, and ask technical questions. The backend uses OpenAI API and advanced prompt engineering to generate realistic, domain-specific responses.

**Key Feature:**  
Each AI mentor is configured with a unique, detailed prompt that strictly limits their expertise and personality, ensuring realistic, role-specific answers and redirection to the appropriate mentor for out-of-domain questions.

---

See each project's folder for more details and setup
