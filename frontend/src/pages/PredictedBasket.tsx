import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Brain, ShoppingCart, TrendingUp, Info, Check, X, 
  RefreshCw, Calendar, Clock, Sparkles, AlertCircle,
  ChevronRight, Plus, Minus, Trash2
} from 'lucide-react';
import { predictionService } from '@/services/prediction.service';
import { cartService } from '@/services/cart.service';
import { useCartStore } from '@/stores/cart.store';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ProductImage from '@/components/products/ProductImage';
import ConfidenceIndicator from '@/components/predictions/ConfidenceIndicator';
import PredictionExplanation from '@/components/predictions/PredictionExplanation';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const PredictedBasket: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { syncWithPredictedBasket } = useCartStore();
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [showExplanations, setShowExplanations] = useState(false);

  // Fetch current predicted basket
  const { data: basket, isLoading, error, refetch } = useQuery(
    'predicted-basket',
    predictionService.getCurrentPredictedBasket,
    {
      staleTime: 5 * 60 * 1000,
      retry: 1
    }
  );

  // Fetch model metrics
  const { data: modelMetrics } = useQuery(
    'model-metrics',
    predictionService.getModelMetrics,
    {
      staleTime: 30 * 60 * 1000
    }
  );

  // Generate new prediction mutation
  const generateMutation = useMutation(
    () => predictionService.generatePrediction({ forceRegenerate: true }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('predicted-basket');
        toast.success('New predictions generated!');
      },
      onError: () => {
        toast.error('Failed to generate predictions');
      }
    }
  );

  // Update item mutation
  const updateItemMutation = useMutation(
    ({ itemId, data }: { itemId: string; data: any }) => 
      predictionService.updateBasketItem(basket!.id, itemId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('predicted-basket');
      }
    }
  );

  // Remove item mutation
  const removeItemMutation = useMutation(
    (itemId: string) => predictionService.removeBasketItem(basket!.id, itemId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('predicted-basket');
        toast.success('Item removed from prediction');
      }
    }
  );

  // Accept basket mutation
  const acceptBasketMutation = useMutation(
    () => predictionService.acceptBasket(basket!.id),
    {
      onSuccess: async (data) => {
        await syncWithPredictedBasket(basket!.id);
        toast.success('Basket accepted! Redirecting to cart...');
        setTimeout(() => navigate('/cart'), 1500);
      },
      onError: () => {
        toast.error('Failed to accept basket');
      }
    }
  );

  // Calculate statistics
  const stats = basket ? {
    totalItems: basket.items.filter(item => item.isAccepted).length,
    totalValue: basket.items
      .filter(item => item.isAccepted)
      .reduce((sum, item) => sum + (item.product.price * item.quantity), 0),
    avgConfidence: basket.items.length > 0
      ? basket.items.reduce((sum, item) => sum + item.confidenceScore, 0) / basket.items.length
      : 0,
    acceptanceRate: basket.items.length > 0
      ? (basket.items.filter(item => item.isAccepted).length / basket.items.length) * 100
      : 0
  } : null;

  const handleQuantityChange = (itemId: string, currentQuantity: number, delta: number) => {
    const newQuantity = Math.max(1, currentQuantity + delta);
    updateItemMutation.mutate({
      itemId,
      data: { quantity: newQuantity }
    });
  };

  const handleToggleItem = (itemId: string, currentAccepted: boolean) => {
    updateItemMutation.mutate({
      itemId,
      data: { isAccepted: !currentAccepted }
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error || !basket) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <Brain className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              No Predictions Available
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              We need more data to generate accurate predictions for you.
            </p>
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isLoading}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {generateMutation.isLoading ? 'Generating...' : 'Generate Predictions'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Your AI-Predicted Basket
                </h1>
                <p className="text-gray-600 dark:text-gray-300">
                  Week of {new Date(basket.weekOf).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowExplanations(!showExplanations)}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Info size={20} />
                {showExplanations ? 'Hide' : 'Show'} Explanations
              </button>
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw size={20} className={generateMutation.isLoading ? 'animate-spin' : ''} />
                Regenerate
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Selected Items</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats?.totalItems || 0}
                  </p>
                </div>
                <ShoppingCart className="w-8 h-8 text-indigo-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Value</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    ${stats?.totalValue.toFixed(2) || '0.00'}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Confidence</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {((stats?.avgConfidence || 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <Sparkles className="w-8 h-8 text-blue-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Accuracy</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats?.acceptanceRate.toFixed(0) || 0}%
                  </p>
                </div>
                <Brain className="w-8 h-8 text-green-500" />
              </div>
            </motion.div>
          </div>

          {/* Model Performance Alert */}
          {modelMetrics && modelMetrics.precisionAt10 > 0.4 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-500 rounded-full">
                  <Check className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-green-900 dark:text-green-100">
                    High Accuracy Predictions
                  </p>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Our model is performing well with {(modelMetrics.precisionAt10 * 100).toFixed(0)}% precision
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Items Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <AnimatePresence>
            {basket.items.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden ${
                  !item.isAccepted ? 'opacity-60' : ''
                }`}
              >
                <div className="p-4">
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="relative">
                      <ProductImage
                        src={item.product.imageUrl}
                        alt={item.product.name}
                        className="w-24 h-24 object-cover rounded-lg"
                      />
                    </div>

                    {/* Product Details */}
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {item.product.name}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {item.product.brand} • {item.product.unit}
                          </p>
                        </div>
                        <button
                          onClick={() => handleToggleItem(item.id, item.isAccepted)}
                          className={`p-2 rounded-lg transition-colors ${
                            item.isAccepted
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-400'
                          }`}
                        >
                          {item.isAccepted ? <Check size={20} /> : <X size={20} />}
                        </button>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">
                            ${item.product.price.toFixed(2)}
                            {item.product.compareAtPrice && (
                              <span className="ml-2 text-sm text-gray-500 line-through">
                                ${item.product.compareAtPrice.toFixed(2)}
                              </span>
                            )}
                          </p>
                          <ConfidenceIndicator score={item.confidenceScore} compact />
                        </div>

                        {/* Quantity Controls */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleQuantityChange(item.id, item.quantity, -1)}
                            disabled={!item.isAccepted}
                            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30"
                          >
                            <Minus size={16} />
                          </button>
                          <span className="w-8 text-center font-semibold">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => handleQuantityChange(item.id, item.quantity, 1)}
                            disabled={!item.isAccepted}
                            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30"
                          >
                            <Plus size={16} />
                          </button>
                          <button
                            onClick={() => removeItemMutation.mutate(item.id)}
                            className="ml-2 p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>

                      {/* Explanation (if enabled) */}
                      {showExplanations && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700"
                        >
                          <PredictionExplanation
                            basketId={basket.id}
                            productId={item.productId}
                            compact
                          />
                        </motion.div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => acceptBasketMutation.mutate()}
            disabled={acceptBasketMutation.isLoading || stats?.totalItems === 0}
            className="flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold rounded-full hover:from-cyan-700 hover:to-blue-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {acceptBasketMutation.isLoading ? (
              <>
                <LoadingSpinner size="small" className="text-white" />
                Processing...
              </>
            ) : (
              <>
                <ShoppingCart size={20} />
                Accept & Add to Cart
                <ChevronRight size={20} />
              </>
            )}
          </button>

          <button
            onClick={() => navigate('/products')}
            className="px-8 py-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white font-bold rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
          >
            Browse More Products
          </button>
        </div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-12 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6"
        >
          <div className="flex gap-4">
            <AlertCircle className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                How it works
              </h3>
              <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <li>• Our AI analyzes your purchase history to predict what you'll need</li>
                <li>• Review and customize the suggestions to match your preferences</li>
                <li>• Accept the basket to add all selected items to your cart at once</li>
                <li>• The more you shop, the better our predictions become!</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PredictedBasket;