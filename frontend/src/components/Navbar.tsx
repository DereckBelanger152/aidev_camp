import { useState } from 'react';
import { Music2, Home, Info, Menu, X } from 'lucide-react';

interface NavbarProps {
  onNavigate?: (page: 'home' | 'about') => void;
}

export const Navbar = ({ onNavigate }: NavbarProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleHomeClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate('home');
    } else {
      window.location.reload();
    }
  };

  const handleAboutClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate('about');
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/30 backdrop-blur-lg border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <a href="/" onClick={handleHomeClick} className="flex items-center gap-3 cursor-pointer">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/50">
              <Music2 className="text-white" size={24} />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
              SoundTwin
            </h1>
          </a>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center gap-6">
            <a
              href="/"
              onClick={handleHomeClick}
              className="flex items-center gap-2 text-white hover:text-pink-400 transition-colors duration-300"
            >
              <Home size={20} />
              <span className="font-medium">Accueil</span>
            </a>
            <a
              href="#"
              onClick={handleAboutClick}
              className="flex items-center gap-2 text-white hover:text-pink-400 transition-colors duration-300"
            >
              <Info size={20} />
              <span className="font-medium">À propos</span>
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden text-white hover:text-pink-400 transition-colors"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="md:hidden mt-4 pb-4 space-y-3 border-t border-white/10 pt-4">
            <a
              href="/"
              className="flex items-center gap-2 text-white hover:text-pink-400 transition-colors duration-300 py-2"
              onClick={(e) => {
                handleHomeClick(e);
                setIsMenuOpen(false);
              }}
            >
              <Home size={20} />
              <span className="font-medium">Accueil</span>
            </a>
            <a
              href="#"
              className="flex items-center gap-2 text-white hover:text-pink-400 transition-colors duration-300 py-2"
              onClick={(e) => {
                handleAboutClick(e);
                setIsMenuOpen(false);
              }}
            >
              <Info size={20} />
              <span className="font-medium">À propos</span>
            </a>
          </div>
        )}
      </div>
    </nav>
  );
};
