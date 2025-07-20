// frontend/src/components/predictions/PredictionExplanation.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, ChevronDown, Calendar, ShoppingCart, TrendingUp } from 'lucide-react';
import { useQuery } from 'react-query';
import { predictionService } from '@/services/prediction.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';

interface PredictionExplanationProps {
  basketId: string;
  productId: string;
  compact?: boolean;
  className?: string;
}

const PredictionExplanation: React.FC<PredictionExplanationProps> = ({
  basketId,
  productId,
  compact = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact);

  const { data: explanation, isLoading } = useQuery(
    ['prediction-explanation', basketId, productId],
    () => predictionService.getPredictionExplanation(basketId, productId),
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
      enabled: !compact || isExpanded
    }
  );

  if (compact && !isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className={`text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 flex items-center gap-1 ${className}`}
      >
        <Info size={14} />
        Why this prediction?
      </button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className={className}
      >
        {compact && (
          <button
            onClick={() => setIsExpanded(false)}
            className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1 mb-2"
          >
            <ChevronDown size={14} className="rotate-180" />
            Hide explanation
          </button>
        )}

        {isLoading ? (
          <div className="flex justify-center py-4">
            <LoadingSpinner size="small" />
          </div>
        ) : explanation ? (
          <div className="space-y-3">
            {/* Confidence Score */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Prediction Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${explanation.confidence * 100}%` }}
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500"
                  />
                </div>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.round(explanation.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Key Factors */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Key Factors
              </h4>
              <div className="space-y-2">
                {explanation.factors.map((factor, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-2"
                  >
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 ${
                      factor.impact > 0.7 ? 'bg-green-500' :
                      factor.impact > 0.4 ? 'bg-yellow-500' :
                      'bg-orange-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {factor.description}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Impact:
                        </span>
                        <div className="flex gap-0.5">
                          {[...Array(5)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-1 h-3 rounded-sm ${
                                i < Math.round(factor.impact * 5)
                                  ? 'bg-indigo-500'
                                  : 'bg-gray-200 dark:bg-gray-700'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Purchase History */}
            {explanation.historicalData && explanation.historicalData.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <Calendar size={14} />
                  Recent Purchase History
                </h4>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {explanation.historicalData.slice(0, 5).map((purchase, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex-shrink-0 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(purchase.date).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: 'numeric' 
                        })}
                      </div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {purchase.quantity}x
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Insights */}
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-start gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    Prediction Insight
                  </p>
                  <p className="text-blue-700 dark:text-blue-300 mt-1">
                    {explanation.confidence >= 0.8
                      ? "This is one of your regular purchases. You typically buy it every 1-2 weeks."
                      : explanation.confidence >= 0.6
                      ? "You buy this product frequently. It's likely you'll need it soon."
                      : "This product matches your shopping patterns, though you buy it less regularly."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Unable to load explanation
          </p>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default PredictionExplanation;