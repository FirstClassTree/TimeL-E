// frontend/src/components/products/ProductImage.tsx

import React, { useState } from 'react';
import { Package, ShoppingBag, Coffee, Apple, Droplets, Shirt, Heart } from 'lucide-react';

interface ProductImageProps {
  src?: string | null;
  alt: string;
  className?: string;
  department?: string;
  onClick?: () => void;
}

const ProductImage: React.FC<ProductImageProps> = ({
  src,
  alt,
  className = '',
  department = '',
  onClick
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(!!src);

  const handleImageError = () => {
    setImageError(true);
    setIsLoading(false);
  };

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  // Get department-themed styling and icon
  const getDepartmentTheme = (dept: string) => {
    const deptLower = dept.toLowerCase();
    
    if (deptLower.includes('produce') || deptLower.includes('fruit') || deptLower.includes('vegetable')) {
      return {
        gradient: 'from-green-400 via-emerald-500 to-teal-600',
        icon: Apple,
        iconColor: 'text-white'
      };
    }
    if (deptLower.includes('dairy') || deptLower.includes('milk') || deptLower.includes('cheese')) {
      return {
        gradient: 'from-blue-400 via-sky-500 to-cyan-600',
        icon: Droplets,
        iconColor: 'text-white'
      };
    }
    if (deptLower.includes('beverage') || deptLower.includes('drink') || deptLower.includes('coffee')) {
      return {
        gradient: 'from-amber-400 via-orange-500 to-red-600',
        icon: Coffee,
        iconColor: 'text-white'
      };
    }
    if (deptLower.includes('personal') || deptLower.includes('care') || deptLower.includes('health')) {
      return {
        gradient: 'from-pink-400 via-rose-500 to-red-600',
        icon: Heart,
        iconColor: 'text-white'
      };
    }
    if (deptLower.includes('household') || deptLower.includes('cleaning') || deptLower.includes('home')) {
      return {
        gradient: 'from-purple-400 via-violet-500 to-indigo-600',
        icon: Shirt,
        iconColor: 'text-white'
      };
    }
    
    // Default theme
    return {
      gradient: 'from-slate-400 via-gray-500 to-zinc-600',
      icon: ShoppingBag,
      iconColor: 'text-white'
    };
  };

  const theme = getDepartmentTheme(department);
  const IconComponent = theme.icon;
  
  // Show image if available and not errored
  const shouldShowImage = src && !imageError;

  return (
    <div 
      className={`relative overflow-hidden bg-gradient-to-br ${theme.gradient} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={{ aspectRatio: '1/1' }} // Force square aspect ratio
    >
      {/* Loading skeleton */}
      {isLoading && shouldShowImage && (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-200 via-gray-300 to-gray-400 animate-pulse" />
      )}
      
      {/* Actual image */}
      {shouldShowImage && (
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            isLoading ? 'opacity-0' : 'opacity-100'
          } ${onClick ? 'cursor-pointer hover:scale-105 transition-transform duration-200' : ''}`}
          onError={handleImageError}
          onLoad={handleImageLoad}
          loading="lazy"
        />
      )}
      
      {/* Beautiful CSS fallback */}
      {!shouldShowImage && (
        <div className="w-full h-full flex items-center justify-center">
          {/* Background pattern */}
          <div className="absolute inset-0 opacity-20">
            <div className="w-full h-full bg-gradient-to-br from-white/30 to-transparent" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent_50%)]" />
          </div>
          
          {/* Icon */}
          <div className="relative z-10 flex flex-col items-center justify-center">
            <IconComponent 
              className={`w-12 h-12 ${theme.iconColor} drop-shadow-lg`}
              strokeWidth={1.5}
            />
            <div className="mt-2 text-xs text-white/80 font-medium text-center px-2">
              {alt.length > 20 ? `${alt.substring(0, 17)}...` : alt}
            </div>
          </div>
          
          {/* Shine effect */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent" />
        </div>
      )}
      
      {/* Hover overlay */}
      {onClick && (
        <div className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors duration-200" />
      )}
    </div>
  );
};

export default ProductImage;
