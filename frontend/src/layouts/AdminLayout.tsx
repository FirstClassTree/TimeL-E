// frontend/src/layouts/AdminLayout.tsx
// UPDATED: Added navigation for User Seeding and enhanced demo features

import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu, X, Home, BarChart3, Users, Package, Settings, 
  ShoppingCart, Shield, LogOut, Brain, Database, Target,
  UserPlus, Zap
} from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';

const AdminLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuthStore();

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
  };

  // Enhanced navigation items with new demo features
  const sidebarItems = [
    {
      label: 'Dashboard',
      path: '/admin/dashboard',
      icon: BarChart3,
      description: 'Overview & analytics'
    },
    {
      label: 'ML Model Metrics',
      path: '/admin/metrics',
      icon: Brain,
      description: 'Performance evaluation',
      highlight: true
    },
    {
      label: 'Demo User Seeding',
      path: '/admin/user-seeding',
      icon: UserPlus,
      description: 'Create demo users',
      highlight: true
    },
    {
      label: 'Live Demo Prediction',
      path: '/admin/demo-prediction',
      icon: Target,
      description: 'Test predictions',
      highlight: true
    },
    {
      label: 'Users',
      path: '/admin/users',
      icon: Users,
      description: 'User management'
    },
    {
      label: 'Products',
      path: '/admin/products',
      icon: Package,
      description: 'Product catalog'
    },
    {
      label: 'Orders',
      path: '/admin/orders',
      icon: Database,
      description: 'Order management'
    },
    {
      label: 'Settings',
      path: '/admin/settings',
      icon: Settings,
      description: 'System configuration'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Menu size={20} />
            </button>
            
            <Link to="/" className="flex items-center gap-2">
              <div className="p-1.5 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-lg">
                <ShoppingCart className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">TimeL-E</span>
                <div className="flex items-center gap-1 text-xs text-cyan-600 dark:text-cyan-400">
                  <Shield size={10} />
                  <span>Admin</span>
                </div>
              </div>
            </Link>
          </div>

          {/* Mobile User Avatar */}
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">
              {user?.name?.[0]?.toUpperCase() || 'A'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <AnimatePresence>
          {(isSidebarOpen || window.innerWidth >= 1024) && (
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ duration: 0.3 }}
              className="fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg lg:shadow-none border-r border-gray-200 dark:border-gray-700"
            >
              {/* Sidebar Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <Link to="/" className="flex items-center gap-2">
                    <div className="p-2 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-lg">
                      <ShoppingCart className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <span className="text-lg font-bold text-gray-900 dark:text-white">TimeL-E</span>
                      <div className="flex items-center gap-1 text-xs text-cyan-600 dark:text-cyan-400">
                        <Shield size={12} />
                        <span>Admin</span>
                      </div>
                    </div>
                  </Link>
                  
                  <button
                    onClick={() => setIsSidebarOpen(false)}
                    className="lg:hidden p-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* User Info */}
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold">
                      {user?.name?.[0]?.toUpperCase() || 'A'}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                      {user?.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Administrator
                    </p>
                  </div>
                </div>
              </div>

              {/* Demo Features Section */}
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <Zap size={16} className="text-yellow-500" />
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    ML Demo Features
                  </h3>
                </div>
                <div className="space-y-1">
                  {sidebarItems.filter(item => item.highlight).map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => window.innerWidth < 1024 && setIsSidebarOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                        location.pathname === item.path
                          ? 'bg-cyan-50 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <item.icon size={18} />
                      <div className="flex-1">
                        <div>{item.label}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {item.description}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>

              {/* Main Navigation */}
              <nav className="p-4 space-y-1">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                  Administration
                </h3>
                {sidebarItems.filter(item => !item.highlight).map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => window.innerWidth < 1024 && setIsSidebarOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'bg-cyan-50 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <item.icon size={18} />
                    {item.label}
                  </Link>
                ))}
              </nav>

              {/* Bottom Actions */}
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
                <Link
                  to="/"
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors mb-2"
                >
                  <Home size={18} />
                  Back to Store
                </Link>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <LogOut size={18} />
                  Sign Out
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 lg:ml-0">
          {/* Overlay for mobile */}
          {isSidebarOpen && (
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}
          
          <main className="p-6 lg:p-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;