import React from "react";
import "../../styles/components/_footer.scss";
export default function Footer() {
  return (
    <footer className="footer">
      © {new Date().getFullYear()} Smart Librarian ~ Andries Andrei
    </footer>
  );
}
