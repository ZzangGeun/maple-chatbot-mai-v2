import React from 'react';
import { Link } from 'react-router-dom';
import '../../styles/globals/common.css';

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo">
          <div className="logo-icon">MAI</div>
          Maple Story Chatbot
        </Link>
      </div>
    </header>
  );
};

export default Header;
