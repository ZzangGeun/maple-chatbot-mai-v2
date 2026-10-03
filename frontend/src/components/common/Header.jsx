import React from 'react';
import { Link } from 'react-router-dom';
import { Leaf } from 'lucide-react';
import Navigation from './Navigation';

const Header = () => (
  <header className="header">
    <div className="header-content">
      <Link to="/" className="logo" aria-label="MAI Help You 홈">
        <span className="logo-icon"><Leaf size={23} strokeWidth={2.5} aria-hidden="true" /></span>
        <span className="logo-wordmark">MAI<span className="logo-caption">HELP YOU</span></span>
      </Link>
      <Navigation />
    </div>
  </header>
);
export default Header;
