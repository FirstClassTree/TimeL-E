// frontend/src/components/auth/AdminRoute.tsx
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth.store';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const AdminRoute: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (!isAuthenticated || !user) {
    // Redirect to login with the current location as state
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user has admin role
  if (user.role !== 'admin') {
    // Redirect to unauthorized page or home
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default AdminRoute;