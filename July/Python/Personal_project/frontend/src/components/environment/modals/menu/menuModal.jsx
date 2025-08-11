// components/environment/modals/menu/MenuModal.jsx
import React from "react";
import "./MenuModal.css";

export default function MenuModal({ onEditProfile, onLogout, onClose }) {
    return (
        <div className="menu-modal-overlay" onClick={onClose}>
            <div className="menu-modal" onClick={(e) => e.stopPropagation()}>
                <div className="menu-buttons">
                    <button onClick={onEditProfile}>My profile</button>
                </div>

                <div className="logout-section">
                    <button className="logout-button" onClick={onLogout}>Logout</button>
                </div>
            </div>
        </div>
    );
}
