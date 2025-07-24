// frontend/src/components/predictions/ConfidenceIndicator.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ConfidenceIndicatorProps {
  score: number;
  showLabel?: boolean;
  showPercentage?: boolean;
  size?: 'small' | 'medium' | 'large';
  compact?: boolean;
  className?: string;
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  score,
  showLabel = true,
  showPercentage = true,
  size = 'medium',
  compact = false,
  className = ''
}) => {
  const getConfidenceLevel = (score: number) => {
    if (score >= 0.8) {
      return {
        level: 'High',
        color: 'green',
        bgColor: 'bg-green-100 dark:bg-green-900/30',
        textColor: 'text-green-700 dark:text-green-300',
        borderColor: 'border-green-300 dark:border-green-700',
        icon: TrendingUp,
        description: 'Very likely to be needed'
      };
    } else if (score >= 0.6) {
      return {
        level: 'Medium',
        color: 'yellow',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
        textColor: 'text-yellow-700 dark:text-yellow-300',
        borderColor: 'border-yellow-300 dark:border-yellow-700',
        icon: Minus,
        description: 'Likely to be needed'
      };
    } else {
      return {
        level: 'Low',
        color: 'orange',
        bgColor: 'bg-orange-100 dark:bg-orange-900/30',
        textColor: 'text-orange-700 dark:text-orange-300',
        borderColor: 'border-orange-300 dark:border-orange-700',
        icon: TrendingDown,
        description: 'Possibly needed'
      };
    }
  };

  const confidence = getConfidenceLevel(score);
  const Icon = confidence.icon;
  const percentage = Math.round(score * 100);

  const sizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 ${sizeClasses[size]} ${className}`}>
        <div className={`w-2 h-2 rounded-full bg-${confidence.color}-500`} />
        <span className={confidence.textColor}>
          {percentage}% confidence
        </span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${confidence.bgColor} ${confidence.borderColor} ${sizeClasses[size]} ${className}`}
    >
      <Icon className={`w-4 h-4 ${confidence.textColor}`} />
      
      {showLabel && (
        <span className={`font-medium ${confidence.textColor}`}>
          {confidence.level}
        </span>
      )}
      
      {showPercentage && (
        <span className={confidence.textColor}>
          ({percentage}%)
        </span>
      )}

      {/* Progress bar */}
      {!compact && size !== 'small' && (
        <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`h-full bg-${confidence.color}-500`}
          />
        </div>
      )}
    </motion.div>
  );
};

export default ConfidenceIndicator;