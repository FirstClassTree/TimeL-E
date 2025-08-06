import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import {Mail, Lock, Eye, EyeOff, ShoppingCart, Loader2, User} from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import { useCartStore } from '@/stores/cart.store';
import toast from 'react-hot-toast';

interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface QuickLoginUser {
  userId: string;
  name: string;
  email: string;
  phone: string;
  password: string,
  avatar: string;
}

const quickLoginUsers: QuickLoginUser[] = [
    {
      userId: "2d8c1a3a-06d5-5f98-84ad-365c7b015ac1",
      name: "John",
      email: "user39993@timele-demo.com",
      password: "password",
      phone: "+1-555-39993",
      avatar: "👨‍💼"
    },
    {
      userId: "8450d218-5822-55af-8818-961027c51a6e",
      name: "Sarah",
      email: "user688@timele-demo.com",
      password: "password",
      phone: "+1-555-688",
      avatar: "👩‍💻"
    },
    {
      userId: "e8f65487-32a9-5c3d-a0b6-716676e25a53",
      name: "Mike",
      email: "user82420@timele-demo.com",
      password: "password",
      phone: "+1-555-82420",
      avatar: "👨‍🎨"
    }
  ];

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, login, isLoading } = useAuthStore();
  const { fetchCart } = useCartStore();
  const [showPassword, setShowPassword] = useState(false)

  const from = (location.state as any)?.from?.pathname || '/';

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError
  } = useForm<LoginFormData>({
    defaultValues: {
      email: '',
      password: '',
      rememberMe: true
    }
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
      
      // Fetch cart after successful login
      const loggedInUser = useAuthStore.getState().user;
      if (loggedInUser?.userId) {
        await fetchCart(loggedInUser.userId);
      }
      
      // Redirect to intended page or home
      navigate(from, { replace: true });
    } catch (error: any) {
      if (error.response?.data?.error) {
        setError('root', { message: error.response.data.error });
      } else {
        toast.error('Login failed. Please try again.');
      }
    }
  };

  const handleQuickLogin = async (quickUser: QuickLoginUser) => {
    try {
      // Use the demo login which will return a random user
      await login(quickUser.email, quickUser.password);
      
      // Fetch cart after successful login
      const loggedInUser = useAuthStore.getState().user;
      if (loggedInUser?.userId) {
        await fetchCart(loggedInUser.userId);
      }
      
      toast.success(`Welcome ${quickUser.name}!`);
      navigate(from, { replace: true });
    } catch (error: any) {
      toast.error('Quick login failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center gap-2 mb-6">
            <div className="p-3 bg-gradient-to-br from-indigo-600 to-blue-600 rounded-2xl">
              <ShoppingCart className="w-8 h-8 text-white" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">TimeL-E</span>
          </Link>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome back
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            Sign in to your account to continue
          </p>
        </div>

        {/* Login Form */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8"
        >
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address'
                    }
                  })}
                  type="email"
                  className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white transition-colors ${
                    errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="you@example.com"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters'
                    }
                  })}
                  type={showPassword ? 'text' : 'password'}
                  className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white transition-colors ${
                    errors.password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  {...register('rememberMe')}
                  type="checkbox"
                  className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Remember me</span>
              </label>
              <Link
                to="/forgot-password"
                className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                Forgot password?
              </Link>
            </div>

            {/* Error Message */}
            {errors.root && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
              >
                <p className="text-sm text-red-600 dark:text-red-400">
                  {errors.root.message}
                </p>
              </motion.div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white font-semibold rounded-lg hover:from-indigo-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-800 text-gray-500">
                  New to TimeL-E?
                </span>
              </div>
            </div>

            {/* Sign Up Link */}
            <Link
              to="/register"
              className="w-full py-3 px-4 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors flex items-center justify-center gap-2"
            >
              Create an Account
            </Link>
          </form>

          {/* Quick Login Users */}
          <div className="mt-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Quick Login
              </p>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {quickLoginUsers.map((quickUser) => (
                <motion.button
                  key={quickUser.userId}
                  onClick={() => handleQuickLogin(quickUser)}
                  disabled={isLoading}
                  className="w-full p-3 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="text-2xl">{quickUser.avatar}</div>
                  <div className="flex-1 text-left">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {quickUser.name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {quickUser.email}
                    </p>
                  </div>
                  {isLoading && userId === quickUser.userId && (
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                  )}
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Footer Links */}
        <div className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
          <Link to="/terms" className="hover:text-gray-900 dark:hover:text-gray-300">
            Terms of Service
          </Link>
          <span className="mx-2">•</span>
          <Link to="/privacy" className="hover:text-gray-900 dark:hover:text-gray-300">
            Privacy Policy
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
