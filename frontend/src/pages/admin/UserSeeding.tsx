// frontend/src/pages/admin/UserSeeding.tsx
// NEW PAGE: Dedicated interface for seeding demo users from Instacart data

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQueryClient } from 'react-query';
import { 
  UserPlus, Database, CheckCircle, AlertCircle, 
  Info, Loader2, Mail, Key, Calendar, Package
} from 'lucide-react';
import { adminService } from '@/services/admin.service';
import toast from 'react-hot-toast';

interface SeedingResult {
  message: string;
  userId: string;
  instacartUserId: string;
  email: string;
  password: string;
  stats: {
    ordersCreated: number;
    orderItemsCreated: number;
    successRate: string;
  };
  loginInstructions: string;
}

const UserSeeding: React.FC = () => {
  const [instacartUserId, setInstacartUserId] = useState<string>('');
  const [seedingResults, setSeedingResults] = useState<SeedingResult[]>([]);
  const queryClient = useQueryClient();

  // Popular Instacart user IDs for quick testing
  const popularUserIds = [
    { id: '1', description: 'Heavy grocery shopper' },
    { id: '7', description: 'Frequent organic buyer' },
    { id: '13', description: 'Family shopper' },
    { id: '25', description: 'Health-conscious buyer' },
    { id: '31', description: 'Bulk shopper' },
    { id: '42', description: 'Diverse preferences' },
    { id: '55', description: 'Regular schedule' },
    { id: '60', description: 'Weekend shopper' },
    { id: '78', description: 'Premium brands' },
    { id: '92', description: 'Convenience focused' }
  ];

  const seedUserMutation = useMutation(adminService.seedDemoUser, {
    onMutate: (userId) => {
      toast.loading(`🌱 Seeding demo user ${userId}... This may take a moment.`, { 
        id: `seed-${userId}`,
        duration: 0
      });
    },
    onSuccess: (data, userId) => {
      toast.dismiss(`seed-${userId}`);
      
      // Add result to the list
      setSeedingResults(prev => [data, ...prev.slice(0, 4)]); // Keep last 5 results
      
      // Clear input
      setInstacartUserId('');
      
      // Invalidate related queries
      queryClient.invalidateQueries(['admin-users']);
      queryClient.invalidateQueries(['dashboard-stats']);
      
      toast.success(`✅ User ${userId} seeded successfully!`, { 
        duration: 6000,
        icon: '🎉'
      });
    },
    onError: (error: any, userId) => {
      toast.dismiss(`seed-${userId}`);
      
      const errorMessage = error.response?.data?.error || 'Failed to seed user';
      const suggestion = error.response?.data?.suggestion || '';
      
      toast.error(`❌ ${errorMessage}${suggestion ? `\n💡 ${suggestion}` : ''}`, { 
        duration: 8000 
      });
    }
  });

  const handleSeedUser = (userId: string) => {
    if (!userId.trim()) {
      toast.error('Please enter a valid Instacart user ID');
      return;
    }
    
    seedUserMutation.mutate(userId.trim());
  };

  const handleQuickSeed = (userId: string) => {
    setInstacartUserId(userId);
    handleSeedUser(userId);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSeedUser(instacartUserId);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg">
              <UserPlus className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Demo User Seeding
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Create demo users with real Instacart shopping history for testing and demonstration purposes. 
            Each user will have their complete order history populated from the original dataset.
          </p>
        </div>

        {/* Info Panel */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <Info className="text-blue-600 dark:text-blue-400 mt-0.5" size={20} />
            <div className="space-y-2">
              <h3 className="font-semibold text-blue-800 dark:text-blue-200">
                How Demo User Seeding Works
              </h3>
              <div className="text-blue-700 dark:text-blue-300 text-sm space-y-1">
                <p>• Enter any Instacart user ID (1-206,209) from the original dataset</p>
                <p>• The system fetches their complete order history from CSV files</p>
                <p>• A new user account is created with proper temporal field mapping</p>
                <p>• All historical orders are populated in the live database</p>
                <p>• The user can then log in and see their "past" orders immediately</p>
                <p>• ML predictions will work based on this seeded history</p>
              </div>
            </div>
          </div>
        </div>

        {/* User Input Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Seed New Demo User
          </h2>
          
          <form onSubmit={handleFormSubmit} className="space-y-6">
            <div>
              <label htmlFor="instacartUserId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Instacart User ID
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="instacartUserId"
                  value={instacartUserId}
                  onChange={(e) => setInstacartUserId(e.target.value)}
                  placeholder="Enter any user ID (e.g., 1, 42, 156789...)"
                  className="flex-1 p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  disabled={seedUserMutation.isLoading}
                />
                <button
                  type="submit"
                  disabled={seedUserMutation.isLoading || !instacartUserId.trim()}
                  className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {seedUserMutation.isLoading ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Database size={16} />
                  )}
                  Seed User
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Quick Seed Options */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Quick Seed - Popular User IDs
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
            These user IDs are known to have rich shopping histories perfect for demonstrations:
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {popularUserIds.map((user) => (
              <button
                key={user.id}
                onClick={() => handleQuickSeed(user.id)}
                disabled={seedUserMutation.isLoading}
                className="p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="font-semibold text-indigo-600 dark:text-indigo-400">
                  User {user.id}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {user.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Recent Seeding Results */}
        <AnimatePresence>
          {seedingResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Recent Seeding Results
              </h2>
              
              <div className="space-y-4">
                {seedingResults.map((result, index) => (
                  <motion.div
                    key={`${result.userId}-${index}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 rounded-lg p-4"
                  >
                    <div className="flex items-start gap-3">
                      <CheckCircle className="text-green-600 dark:text-green-400 mt-0.5" size={20} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-green-800 dark:text-green-200">
                            Demo User Created Successfully
                          </h3>
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-300 text-xs rounded-full">
                            Instacart ID: {result.instacartUserId}
                          </span>
                        </div>
                        
                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                              <Mail size={14} />
                              <span className="font-mono">{result.email}</span>
                            </div>
                            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                              <Key size={14} />
                              <span className="font-mono">{result.password}</span>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                              <Calendar size={14} />
                              <span>{result.stats.ordersCreated} orders created</span>
                            </div>
                            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                              <Package size={14} />
                              <span>{result.stats.orderItemsCreated} items seeded</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="mt-3 p-3 bg-green-100 dark:bg-green-800/50 rounded text-xs text-green-700 dark:text-green-300">
                          <strong>Login Instructions:</strong> Use the email and password above to log in. 
                          The user will see their complete order history as if they've been using the app for months!
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Usage Instructions */}
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
            Complete Demo Workflow
          </h3>
          <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <div>
                <strong>Seed Demo User:</strong> Enter an Instacart user ID and click "Seed User"
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <div>
                <strong>User Login:</strong> Use the generated email and password to log in as the demo user
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <div>
                <strong>View Order History:</strong> The user will see their complete shopping history
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <div>
                <strong>Generate Predictions:</strong> Use the "Predict Next Basket" feature to see ML recommendations
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserSeeding;