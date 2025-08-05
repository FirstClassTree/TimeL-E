import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ShoppingCart, Heart, Star, Plus, Minus, ArrowLeft,
  Package, Truck, Shield, Info
} from 'lucide-react';
import { productService } from '@/services/product.service';
import { useCartStore } from '@/stores/cart.store';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ProductImage from '@/components/products/ProductImage';
import toast from 'react-hot-toast';
import { useUser } from '@/components/auth/UserProvider'

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToCart } = useCartStore();
  const {userId} = useUser();
  const [quantity, setQuantity] = useState(1);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const { data: product, isLoading, error } = useQuery(
    ['product', id],
    () => productService.getProduct(product?.productId ?? Number(id)),
    {
      enabled: !!id,
    }
  );

  const handleAddToCart = () => {
    if (!product) return;
    
    addToCart(userId,
        product.productId,
      quantity
    );
    
    toast.success(`Added ${quantity} ${product.productName} to cart`);
  };

  const handleBuyNow = () => {
    handleAddToCart();
    navigate('/cart');
  };

  if (isLoading) return <LoadingSpinner fullScreen />;
  if (error || !product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Product not found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The product you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/products')}
            className="flex items-center gap-2 mx-auto bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Products
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 transition-colors"
        >
          <ArrowLeft size={16} />
          Back
        </button>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Product Images */}
        <div className="space-y-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800"
          >
            <ProductImage
              src={product.imageUrl}
              alt={product.productName}
              className="w-full h-full object-cover"
            />
          </motion.div>

          {/* Additional product images would go here if available */}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {product.productName}
            </h1>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    size={18}
                    className={`${
                      i < 4 ? 'text-yellow-400 fill-current' : 'text-gray-300 dark:text-gray-600'
                    }`}
                  />
                ))}
                <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">
                  4.0 (24 reviews)
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 mb-6">
              <span className="text-3xl font-bold text-gray-900 dark:text-white">
                ${product.price}
              </span>
              {(product?.price ?? 0) > 20 && (
                <span className="text-lg text-gray-500 dark:text-gray-400 line-through">
                  ${((product?.price ?? 0) * 1.2).toFixed(2)}
                </span>
              )}
              <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-sm font-medium rounded">
                In Stock
              </span>
            </div>

            <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
              {product.description || 'High-quality product with excellent value and taste. Perfect for your daily needs.'}
            </p>

            {/* Quantity Selector */}
            <div className="flex items-center gap-4 mb-6">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Quantity:
              </span>
              <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <Minus size={16} />
                </button>
                <span className="px-4 py-2 font-medium text-gray-900 dark:text-white">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 mb-8">
              <button
                onClick={handleAddToCart}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                <ShoppingCart size={20} />
                Add to Cart
              </button>
              <button
                onClick={handleBuyNow}
                className="flex items-center gap-2 px-6 py-3 bg-gray-900 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-800 dark:hover:bg-gray-600 transition-colors font-medium"
              >
                Buy Now
              </button>
              <button className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <Heart size={20} />
              </button>
            </div>

            {/* Product Features */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <Truck className="text-indigo-600 dark:text-indigo-400" size={20} />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                    Free Delivery
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    On orders over $35
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <Shield className="text-green-600 dark:text-green-400" size={20} />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                    Quality Assured
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Fresh guarantee
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <Package className="text-blue-600 dark:text-blue-400" size={20} />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                    Easy Returns
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    30-day policy
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Product Details */}
      <div className="mt-16">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Product Details
          </h3>
        </div>
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">
              Specifications
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Category:</span>
                <span className="text-gray-900 dark:text-white">{product.departmentName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Brand:</span>
                <span className="text-gray-900 dark:text-white">Premium</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">SKU:</span>
                <span className="text-gray-900 dark:text-white">PRD-{product.productId}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">
              Nutrition Information
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Calories:</span>
                <span className="text-gray-900 dark:text-white">Per serving</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Storage:</span>
                <span className="text-gray-900 dark:text-white">Cool, dry place</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Shelf Life:</span>
                <span className="text-gray-900 dark:text-white">12 months</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;