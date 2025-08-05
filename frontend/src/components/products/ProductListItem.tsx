import React from 'react';
import { Link } from 'react-router-dom';
import { ShoppingCart } from 'lucide-react';
import { Product } from '@/services/product.service';
import { useCartStore } from '@/stores/cart.store';
import { useAuthStore } from '@/stores/auth.store';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { useUser } from '@/components/auth/UserProvider';
import ProductImage from '@/components/products/ProductImage';

interface ProductListItemProps {
  product: Product;
}

const ProductListItem: React.FC<ProductListItemProps> = ({ product }) => {
  const { addToCart } = useCartStore();
  const { user, isAuthenticated } = useAuthStore();
  const { userId } = useUser();

  const addToCartMutation = useMutation(
    () => addToCart(user?.userId ?? userId, product.productId),
    {
      onSuccess: () => {
        toast.success('Added to cart');
      },
      onError: () => {
        toast.error('Failed to add to cart');
      }
    }
  );

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart');
      return;
    }
    
    addToCartMutation.mutate();
  };

  const discount = 0;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow">
      <Link to={`/products/${product.productId}`} className="block">
        <div className="flex p-4">
          {/* Product Image */}
          <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden">
            <ProductImage
              src={product.imageUrl}
              alt={product.productName}
              department={product.departmentName}
              className="w-full h-full"
            />
          </div>
          
          {/* Product Info */}
          <div className="flex-1 ml-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                  {product.productName}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {product.departmentName} • {product.aisleName}
                </p>
                {product.description && (
                  <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                    {product.description}
                  </p>
                )}
                
                {/* Price */}
                <div className="flex items-center gap-2 mt-2">
                  <span className="font-bold text-gray-900 dark:text-white">
                    ${product.price?.toFixed(2)}
                  </span>
                  {product.price && (
                    <>
                      <span className="text-xs text-gray-500 line-through">
                        ${product.price.toFixed(2)}
                      </span>
                      {discount > 0 && (
                        <span className="text-xs font-medium text-red-600 dark:text-red-400">
                          -{discount}%
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex flex-col gap-2 ml-4">
                {/* Add to Cart */}
                <button
                  onClick={handleAddToCart}
                  disabled={addToCartMutation.isLoading}
                  className={`p-2 rounded-full transition-all ${
                    'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/30'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title='Add to cart'
                >
                  <ShoppingCart size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
};

export default ProductListItem;
