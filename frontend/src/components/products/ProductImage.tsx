// frontend/src/components/products/ProductImage.tsx

import React, { useState } from 'react';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import { Package } from 'lucide-react';
import 'react-lazy-load-image-component/src/effects/blur.css';

interface ProductImageProps {
  src?: string | null;
  alt: string;
  className?: string;
  fallbackIcon?: React.ElementType;
  onClick?: () => void;
}

const ProductImage: React.FC<ProductImageProps> = ({
  src,
  alt,
  className = '',
  fallbackIcon: FallbackIcon = Package,
  onClick
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const handleImageError = () => {
    setImageError(true);
    setIsLoading(false);
  };

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  // ✅ FIXED: Use external placeholder instead of deleted local file
  const placeholderImage = './app/storage/image_not_available.png';
  const imageSrc = src || placeholderImage;

  // ✅ FIXED: Removed reference to deleted '/images/products/default.jpg'
  if (imageError || !imageSrc) {
    return (
      <div 
        className={`flex items-center justify-center bg-gray-100 dark:bg-gray-800 ${className}`}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
      >
        <FallbackIcon className="w-12 h-12 text-gray-400" />
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-100 dark:bg-gray-800 animate-pulse" />
      )}
      <LazyLoadImage
        src={imageSrc}
        alt={alt}
        effect="blur"
        className={`w-full h-full object-cover ${onClick ? 'cursor-pointer' : ''}`}
        onError={handleImageError}
        afterLoad={handleImageLoad}
        onClick={onClick}
        placeholderSrc="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Crect width='400' height='400' fill='%23f3f4f6'/%3E%3C/svg%3E"
      />
    </div>
  );
};

export default ProductImage;