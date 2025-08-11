import React, { useState } from "react";
import { jwtDecode } from "jwt-decode";
import { useAuthProvider } from "../../hooks";

export default function Login({ onLogin }) {

    const [rememberMe, setRememberMe] = useState(true);
    const handleSetRememberMe = () => setRememberMe(!rememberMe);

    const { setUser, setToken } = useAuthProvider();

    const [formValue, setFormValue] = useState({
        email: "",
        password: "",
    });
    const [error, setError] = useState("");

    const handleChange = (e) => {
        setError('')
        const { name, value } = e.target;
        setFormValue((prev) => {
            return { ...prev, [name]: value };
        });
    };

    const checkErrors = (field) => {
        let error = "";
        if (field === "email") {
            let reg = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w\w+)+$/;
            if (reg.test(formValue.email) === false) error = "true";
        }

        if (field === "password") {
            if (formValue.password.length === 0) error = "true";
        }

        return error;
    };
    const isFormValid = () => {
        let isValid = true;
        Object.keys(formValue).forEach((field) => {
            if (checkErrors(field)) {
                isValid = false;
            }
        });
        return isValid;
    };

    const handleLogin = async () => {
        if(!isFormValid()){
            setError("Something is wrong with your credentials")
        }
        if (isFormValid()) {
            try {
                const apiUrl = import.meta.env.VITE_API_URL;
                const response = await fetch(`${apiUrl}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formValue)
                });

                if (!response.ok) {
                    throw new Error("Invalid credentials.");
                }
                // console.log(response.json())
                const data = await response.json();
                const token = data.token;

                const decodedToken = jwtDecode(token);

                if (rememberMe) localStorage.setItem("token", token);
                else sessionStorage.setItem("token", token);
                setUser(decodedToken);
                onLogin(token);
            } catch (err) {
                setError(err.message);
            }
        }
    }

    return (
        <div className="login-modal">
            <div className="form-content">
                <h2>Login form</h2>
                <label htmlFor="email">Email</label>
                <input
                    type="text"
                    placeholder="Email"
                    name="email"
                    id="email"
                    autoComplete="on"
                    value={formValue.email}
                    onChange={handleChange}
                />

                <label htmlFor="password">Password</label>
                <input
                    type="password"
                    placeholder="Password"
                    id="password"
                    name="password"
                    autoComplete="on"
                    value={formValue.password}
                    onChange={handleChange}
                />


                <div className="remember-me" onClick={handleSetRememberMe}>
                    <label htmlFor="rememberMe" className="remember-me-text">
                        Remember me:
                    </label>
                    <input
                        type="checkbox"
                        id="rememberMe"
                        defaultChecked
                    />
                </div>

                {error && <small className="form-error">{error}</small>}
            </div>
            <div className="form-buttons" onClick={handleLogin}>
                <button>Login</button>
            </div>
        </div>
    );
}
