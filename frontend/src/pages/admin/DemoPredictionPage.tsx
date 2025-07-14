// frontend/src/pages/admin/DemoPredictionPage.tsx
// ENHANCED: Improved UX for any user ID input with better error handling and suggestions

import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { adminService, DemoUserPrediction } from '@/services/admin.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ProductImage from '@/components/products/ProductImage';
import { 
  Brain, CheckCircle, AlertCircle, RefreshCw, Search, 
  Info, TrendingUp, Target, Zap, ArrowRight, Sparkles 
} from 'lucide-react';
import toast from 'react-hot-toast';

const DemoPredictionPage: React.FC = () => {
    const [userIdInput, setUserIdInput] = useState<string>('');
    const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
    const [showSuggestions, setShowSuggestions] = useState(true);

    // Enhanced user ID suggestions with descriptions
    const enhancedSuggestions = [
        { id: '1', description: 'Heavy grocery shopper', orders: '40+ orders' },
        { id: '7', description: 'Organic food enthusiast', orders: '35+ orders' },
        { id: '13', description: 'Family bulk buyer', orders: '50+ orders' },
        { id: '25', description: 'Health-conscious shopper', orders: '30+ orders' },
        { id: '31', description: 'Weekend regular', orders: '25+ orders' },
        { id: '42', description: 'Diverse preferences', orders: '45+ orders' },
        { id: '55', description: 'Premium brand lover', orders: '20+ orders' },
        { id: '60', description: 'Quick convenience shopper', orders: '55+ orders' },
        { id: '78', description: 'International cuisine fan', orders: '35+ orders' },
        { id: '92', description: 'Meal prep specialist', orders: '30+ orders' }
    ];

    // Get demo system metadata
    const { data: demoUserMetadata } = useQuery('demoUserMetadata', adminService.getDemoUserIds);

    // Get prediction data for selected user
    const { 
        data: demoPredictionData, 
        isLoading: isLoadingPrediction, 
        error: predictionError,
        refetch: refetchPrediction,
        isError 
    } = useQuery(
        ['demoUserPrediction', selectedUserId],
        () => adminService.getDemoUserPrediction(selectedUserId!),
        { 
            enabled: !!selectedUserId,
            retry: 1,
            staleTime: 30000
        }
    );

    const handleUserIdSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (userIdInput.trim()) {
            const userId = userIdInput.trim();
            setSelectedUserId(userId);
            setShowSuggestions(false);
            refetchPrediction();
        } else {
            toast.error("Please enter a valid Instacart user ID.");
        }
    };

    const handleSuggestionClick = (userId: string) => {
        setUserIdInput(userId);
        setSelectedUserId(userId);
        setShowSuggestions(false);
        refetchPrediction();
    };

    const handleTryAnother = () => {
        setSelectedUserId(null);
        setUserIdInput('');
        setShowSuggestions(true);
    };

    const renderProductList = (title: string, products: any[], isPredicted = false, icon: React.ReactNode) => (
        <div className="w-full lg:w-1/2 px-2">
            <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 h-full ${
                isPredicted 
                    ? 'border-l-4 border-indigo-500' 
                    : 'border-l-4 border-green-500'
            }`}>
                <div className="flex items-center gap-3 mb-6">
                    {icon}
                    <h3 className={`text-xl font-semibold ${
                        isPredicted 
                            ? 'text-indigo-800 dark:text-indigo-200' 
                            : 'text-green-800 dark:text-green-200'
                    }`}>
                        {title}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        isPredicted
                            ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300'
                            : 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                    }`}>
                        {products?.length || 0} items
                    </span>
                </div>
                
                {products && products.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {products.slice(0, 8).map((product: any, index: number) => (
                            <motion.div
                                key={product.id || index}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                            >
                                <ProductImage
                                    src={product.imageUrl}
                                    alt={product.name}
                                    className="w-12 h-12 object-cover rounded"
                                />
                                <div className="flex-1 min-w-0">
                                    <h4 className="font-medium text-gray-900 dark:text-white text-sm truncate">
                                        {product.name}
                                    </h4>
                                    <div className="flex items-center justify-between mt-1">
                                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                            {product.category}
                                        </p>
                                        <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                            ${Number(product.price || 0).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                        {products.length > 8 && (
                            <div className="col-span-full text-center text-sm text-gray-500 dark:text-gray-400 py-2">
                                ... and {products.length - 8} more items
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        <AlertCircle size={48} className="mx-auto mb-3 opacity-50" />
                        <p>No {isPredicted ? 'predictions' : 'ground truth data'} available</p>
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto space-y-8">
                
                {/* Header */}
                <div className="text-center">
                    <div className="flex items-center justify-center gap-3 mb-4">
                        <div className="p-3 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg">
                            <Brain className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                            Live Demo Prediction
                        </h1>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
                        Enter any Instacart user ID to see our ML model predict their next basket compared to their actual future purchases.
                        This demonstrates real-time prediction accuracy using the original dataset.
                    </p>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div className="flex items-start gap-3">
                        <Info className="text-blue-600 dark:text-blue-400 mt-0.5" size={20} />
                        <div>
                            <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                                How Live Demo Works
                            </h3>
                            <div className="text-blue-700 dark:text-blue-300 text-sm space-y-1">
                                <p>• Enter any user ID from the Instacart dataset (1 to 206,209)</p>
                                <p>• Our ML model analyzes their shopping history from CSV data</p>
                                <p>• The system generates basket predictions and compares with actual purchases</p>
                                <p>• See real accuracy metrics: precision, recall, and item overlap</p>
                            </div>
                            {demoUserMetadata?.message && (
                                <div className="mt-3 p-3 bg-blue-100 dark:bg-blue-800 rounded text-blue-800 dark:text-blue-200">
                                    <strong>System Status:</strong> {demoUserMetadata.message}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* User ID Input Form */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                    <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">
                        Select User for Prediction Demo
                    </h2>
                    
                    <form onSubmit={handleUserIdSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="userIdInput" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Enter Instacart User ID:
                            </label>
                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    id="userIdInput"
                                    value={userIdInput}
                                    onChange={(e) => setUserIdInput(e.target.value)}
                                    placeholder="e.g., 1, 42, 1337, 156789..."
                                    className="flex-1 p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    disabled={isLoadingPrediction}
                                />
                                <button
                                    type="submit"
                                    disabled={isLoadingPrediction || !userIdInput.trim()}
                                    className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoadingPrediction ? (
                                        <RefreshCw size={16} className="animate-spin" />
                                    ) : (
                                        <Search size={16} />
                                    )}
                                    {isLoadingPrediction ? 'Analyzing...' : 'Predict'}
                                </button>
                            </div>
                        </div>
                    </form>

                    {/* Quick Suggestions */}
                    <AnimatePresence>
                        {showSuggestions && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mt-6"
                            >
                                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                    Quick Demo - Popular User IDs:
                                </h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                                    {enhancedSuggestions.map((suggestion) => (
                                        <button
                                            key={suggestion.id}
                                            onClick={() => handleSuggestionClick(suggestion.id)}
                                            disabled={isLoadingPrediction}
                                            className="p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                                        >
                                            <div className="font-semibold text-indigo-600 dark:text-indigo-400">
                                                User {suggestion.id}
                                            </div>
                                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                {suggestion.description}
                                            </div>
                                            <div className="text-xs text-gray-400 dark:text-gray-500">
                                                {suggestion.orders}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Loading State */}
                {isLoadingPrediction && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8"
                    >
                        <div className="text-center">
                            <div className="flex items-center justify-center gap-3 mb-4">
                                <RefreshCw className="animate-spin text-indigo-600" size={24} />
                                <span className="text-lg font-medium text-gray-900 dark:text-white">
                                    Analyzing User {selectedUserId}...
                                </span>
                            </div>
                            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                                <p>• Loading order history from CSV data</p>
                                <p>• Generating ML features</p>
                                <p>• Running prediction model</p>
                                <p>• Fetching ground truth data</p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Error State */}
                {isError && predictionError && !isLoadingPrediction && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6"
                    >
                        <div className="flex items-start gap-3">
                            <AlertCircle className="text-red-600 dark:text-red-400 mt-0.5" size={20} />
                            <div className="flex-1">
                                <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">
                                    Prediction Failed
                                </h3>
                                <p className="text-red-700 dark:text-red-300 text-sm mb-4">
                                    {(predictionError as any)?.response?.data?.detail || 
                                     `User ${selectedUserId} not found in the Instacart dataset.`}
                                </p>
                                <div className="flex gap-3">
                                    <button
                                        onClick={handleTryAnother}
                                        className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                                    >
                                        Try Another User
                                    </button>
                                    <button
                                        onClick={() => refetchPrediction()}
                                        className="px-4 py-2 border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 text-sm rounded-md hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
                                    >
                                        Retry
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Prediction Results */}
                {demoPredictionData && !isLoadingPrediction && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Success Header */}
                        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
                            <div className="flex items-center gap-3 mb-4">
                                <CheckCircle className="text-green-600 dark:text-green-400" size={24} />
                                <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
                                    Prediction Analysis Complete for User {selectedUserId}! 🎯
                                </h3>
                            </div>
                            
                            {/* Comparison Metrics */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                        {demoPredictionData.comparisonMetrics.predictedCount}
                                    </div>
                                    <div className="text-sm text-green-700 dark:text-green-300">Predicted Items</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                        {demoPredictionData.comparisonMetrics.actualCount}
                                    </div>
                                    <div className="text-sm text-green-700 dark:text-green-300">Actual Items</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                        {demoPredictionData.comparisonMetrics.commonItems}
                                    </div>
                                    <div className="text-sm text-green-700 dark:text-green-300">Matches</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                        {demoPredictionData.comparisonMetrics.accuracy?.toFixed(1) || 
                                         ((demoPredictionData.comparisonMetrics.commonItems / 
                                           Math.max(demoPredictionData.comparisonMetrics.actualCount, 1)) * 100).toFixed(1)}%
                                    </div>
                                    <div className="text-sm text-green-700 dark:text-green-300">Accuracy</div>
                                </div>
                            </div>
                        </div>

                        {/* Side-by-Side Comparison */}
                        <div className="flex flex-col lg:flex-row gap-6">
                            {renderProductList(
                                "ML Model Prediction", 
                                demoPredictionData.predictedBasket,
                                true,
                                <Brain className="text-indigo-600 dark:text-indigo-400" size={24} />
                            )}
                            {renderProductList(
                                "Actual Future Basket", 
                                demoPredictionData.trueFutureBasket,
                                false,
                                <Target className="text-green-600 dark:text-green-400" size={24} />
                            )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex justify-center gap-4">
                            <button
                                onClick={handleTryAnother}
                                className="flex items-center gap-2 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                <ArrowRight size={16} />
                                Try Another User
                            </button>
                            <button
                                onClick={() => refetchPrediction()}
                                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                            >
                                <RefreshCw size={16} />
                                Refresh Prediction
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* No results yet */}
                {!selectedUserId && !isLoadingPrediction && (
                    <div className="text-center py-12">
                        <Sparkles className="mx-auto mb-4 text-gray-400" size={48} />
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                            Ready for Demo
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">
                            Enter a user ID above or click one of the suggested users to see live ML predictions!
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DemoPredictionPage;