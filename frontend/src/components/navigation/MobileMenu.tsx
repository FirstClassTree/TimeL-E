// frontend/src/components/navigation/MobileMenu.tsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LucideIcon, User, Package, Heart, ShoppingCart, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';

interface NavLink {
  path: string;
  label: string;
  icon: LucideIcon;
  authRequired?: boolean;
}

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  navLinks: NavLink[];
}

const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose, navLinks }) => {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    onClose();
  };

  const handleLinkClick = () => {
    onClose();
  };

  return (
    <motion.div
      initial={{ x: '-100%' }}
      animate={{ x: 0 }}
      exit={{ x: '-100%' }}
      transition={{ type: 'tween', duration: 0.3 }}
      className="fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 -z-10"
        onClick={onClose}
      />

      {/* Menu Content */}
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">
                  {user.firstName[0]?.toUpperCase()}{user.lastName[0]?.toUpperCase()}
                </span>
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {user.firstName} {user.lastName}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {user.emailAddress}
                </p>
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Welcome to TimeL-E
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Sign in to get started
              </p>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-4 space-y-2">
          {navLinks.map((link) => {
            if (link.authRequired && !isAuthenticated) return null;
            
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={handleLinkClick}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                  location.pathname === link.path
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <link.icon size={20} />
                <span className="font-medium">{link.label}</span>
              </Link>
            );
          })}

          {/* Additional User Links */}
          {isAuthenticated && (
            <>
              <div className="border-t border-gray-200 dark:border-gray-700 my-4"></div>
              
              <Link
                to="/profile"
                onClick={handleLinkClick}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                  location.pathname === '/profile'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <User size={20} />
                <span className="font-medium">My Profile</span>
              </Link>

              <Link
                to="/orders"
                onClick={handleLinkClick}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                  location.pathname === '/orders'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Package size={20} />
                <span className="font-medium">My Orders</span>
              </Link>

              <Link
                to="/favorites"
                onClick={handleLinkClick}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                  location.pathname === '/favorites'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Heart size={20} />
                <span className="font-medium">Favorites</span>
              </Link>

              <Link
                to="/cart"
                onClick={handleLinkClick}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                  location.pathname === '/cart'
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <ShoppingCart size={20} />
                <span className="font-medium">Cart</span>
              </Link>
            </>
          )}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-3 py-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <LogOut size={20} />
              <span className="font-medium">Sign Out</span>
            </button>
          ) : (
            <div className="space-y-2">
              <Link
                to="/login"
                onClick={handleLinkClick}
                className="block w-full text-center px-4 py-2 text-indigo-600 dark:text-indigo-400 border border-indigo-600 dark:border-indigo-400 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                onClick={handleLinkClick}
                className="block w-full text-center px-4 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MobileMenu;