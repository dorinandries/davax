// src/components/environment/modals/userForm.jsx
import React, { useState } from "react";
import "./userModal.css";
import { useAuthProvider } from "../../../../hooks";

export default function UserForm({ onClose }) {
    const { user, loadUser, token } = useAuthProvider();
    const [form, setForm] = useState({
        userID: user?.userID,
        role: user?.role || "",
        seniority: user?.seniority || "",
        experience: user?.experience || "",
    });
    const [error, setError] = useState("");

    const validateForm = () => {
        if (!form.role || !form.seniority || !form.experience) {
            setError("Toate câmpurile sunt obligatorii");
            return false;
        }
        setError("");
        return true;
    };

    const handleSubmit = async () => {
        if (!validateForm()) return;
        try {
            const apiUrl = import.meta.env.VITE_API_URL;
            const res = await fetch(`${apiUrl}/update-user`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(form),
            });
            if (res.status !== 200) {
                const errText = await res.text();
                throw new Error(errText || "Eroare la salvarea profilului");
            }
            // preluăm răspunsul cu user-ul actualizat
            const updatedUser = await res.json();
            // încărcăm din nou contextul
            loadUser(updatedUser?.user_id, token);
            onClose();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleChange = (e) => {
        setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    };

    return (
        <div className="user-form-modal">
            <div className="form-content">
                <h2>My profile</h2>
                <label>Role</label>
                <input name="role" value={form.role} onChange={handleChange} />

                <label>Experience</label>
                <input
                    name="experience"
                    value={form.experience}
                    onChange={handleChange}
                />

                <label>Seniority</label>
                <input
                    name="seniority"
                    value={form.seniority}
                    onChange={handleChange}
                />

                {error && <div className="form-error">{error}</div>}

                <div className="form-buttons">
                    <button onClick={handleSubmit}>Save</button>
                </div>

                <div className="form-buttons">
                    <button onClick={onClose}>Close</button>
                </div>
            </div>
        </div >
    );
}
