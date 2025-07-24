import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingCart, Eye } from 'lucide-react';
import { Product } from '@/services/product.service';
import { useCartStore } from '@/stores/cart.store';
import { useAuthStore } from '@/stores/auth.store';
import ProductImage from '@/components/products/ProductImage';
import toast from 'react-hot-toast';
import {useUser} from "@/components/auth/UserProvider.tsx";

interface ProductCardProps {
  product: Product;
  variant?: 'default' | 'compact' | 'detailed';
}

const ProductCard: React.FC<ProductCardProps> = ({ product}) => {
  const [isHovered, setIsHovered] = useState(false);
  const { user, isAuthenticated } = useAuthStore();
  const { addToCart, isProductInCart, isUpdating } = useCartStore();
  const {userId } = useUser();
  const isInCart = isProductInCart(product.product_id);

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart');
      return;
    }

    try {
      await addToCart(user?.id ?? userId ,product.product_id);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden h-full flex flex-col"
    >
      <Link to={`/products/${product.product_id}`} className="block">
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700">
          <ProductImage
            src={product.image_url}
            alt={product.product_name}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: isHovered ? 1 : 0 }}
            transition={{ duration: 0.2 }}
            className="absolute top-3 right-3 flex flex-col gap-2"
          >
            <Link
              to={`/products/${product.product_id}`}
              className="p-2 bg-white/80 dark:bg-gray-800/80 rounded-full backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-indigo-500 hover:text-white transition-all"
            >
              <Eye size={18} />
            </Link>
          </motion.div>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Category & Brand */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {product.department_name}
            </span>
            {product.aisle_name && (
              <>
                <span className="text-xs text-gray-400">•</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {product.aisle_name}
                </span>
              </>
            )}
          </div>

          {/* Product Name */}
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
            {product.product_name}
          </h3>

          {/* Product Description */}
          {product.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
              {product.description}
            </p>
          )}

          {/* Price Section */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                ${product?.price==null ? 0  : product?.price.toFixed(2)}
              </span>
              {product.price && (
                <span className="text-sm text-gray-500 line-through">
                  ${product.price.toFixed(2)}
                </span>
              )}
            </div>
          </div>

          {/* Add to Cart Button */}
          <button
            onClick={handleAddToCart}
            disabled={isUpdating}
            className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${
              isInCart
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <ShoppingCart size={18} />
            {isUpdating ? (
              'Adding...'
            ) : isInCart ? (
              'In Cart'
            ) : (
              'Add to Cart'
            )}
          </button>
        </div>
      </Link>
    </motion.div>
  );
};

export default ProductCard;
