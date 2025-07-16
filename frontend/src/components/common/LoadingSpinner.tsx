// frontend/src/components/common/LoadingSpinner.tsx
import React from 'react';
import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
  fullScreen?: boolean;
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = 'indigo',
  className = '',
  fullScreen = false,
  message
}) => {
  const sizes = {
    small: 'w-6 h-6',
    medium: 'w-10 h-10',
    large: 'w-16 h-16'
  };

  const spinnerContent = (
    <div className={`${fullScreen ? 'flex flex-col items-center justify-center h-screen' : ''} ${className}`}>
      <motion.div
        className={`${sizes[size]} relative`}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <div className={`absolute inset-0 rounded-full border-4 border-${color}-200 dark:border-${color}-800`} />
        <div className={`absolute inset-0 rounded-full border-4 border-t-${color}-600 border-r-transparent border-b-transparent border-l-transparent`} />
      </motion.div>
      {message && (
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className={`mt-4 text-${size === 'small' ? 'sm' : size === 'large' ? 'lg' : 'base'} text-gray-600 dark:text-gray-400`}
        >
          {message}
        </motion.p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-50">
        {spinnerContent}
      </div>
    );
  }

  return spinnerContent;
};

export default LoadingSpinner;