import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingCart, Trash2, Plus, Minus, ArrowRight, 
  Package, CheckCircle, Truck
} from 'lucide-react';
import { useCartStore } from '@/stores/cart.store';
import { useAuthStore } from '@/stores/auth.store';
import ProductImage from '@/components/products/ProductImage';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';
import toast from 'react-hot-toast';
import { useUser } from '@/components/auth/UserProvider';

const Cart: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { 
    cart, 
    isLoading, 
    isUpdating,
    fetchCart, 
    updateQuantity, 
    removeItem, 
    clearCart,
    getSubtotal
  } = useCartStore();
  const { userId } = useUser();

  useEffect(() => {
    fetchCart(user?.userId ?? userId);
  }, []);

  const handleQuantityChange = async (itemId: number, currentQuantity: number, delta: number) => {
    const newQuantity = currentQuantity + delta;
    if (newQuantity < 1) {
      await removeItem(user?.userId ?? userId, itemId);
    } else {
      await updateQuantity(user?.userId ?? userId, itemId, newQuantity);
    }
  };

  const handleCheckout = () => {
    if (!cart || cart.items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    navigate('/checkout');
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      try {
        await clearCart(user?.userId ?? userId);
      } catch (error) {
        console.error('Failed to clear cart:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <EmptyState
        icon={ShoppingCart}
        title="Your cart is empty"
        description="Add some products to your cart to get started"
        action={{
          label: "Browse Products",
          onClick: () => navigate('/products')
        }}
      />
    );
  }

  const subtotal = getSubtotal();
  const estimatedTax = subtotal * 0.18; // 18% tax
  const deliveryFee = 7.99;
  const total = subtotal + estimatedTax + deliveryFee;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Shopping Cart</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {cart.items.length} {cart.items.length === 1 ? 'item' : 'items'} in your cart
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Items in your cart
                  </h2>
                  <button
                    onClick={handleClearCart}
                    disabled={isUpdating}
                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm font-medium flex items-center gap-1 disabled:opacity-50"
                  >
                    <Trash2 size={14} />
                    Clear cart
                  </button>
                </div>
              </div>

              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                <AnimatePresence mode="popLayout">
                  {cart.items.map((item) => (
                    <motion.div
                      key={item.id}
                      layout
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="p-6"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-20 h-20 flex-shrink-0">
                          <ProductImage
                            src={item.product.image_url}
                            alt={item.product.product_name}
                            className="w-full h-full object-cover rounded-lg"
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="text-base font-medium text-gray-900 dark:text-white truncate">
                                {item.product.product_name}
                              </h3>
                              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                {item.product.department_name}
                              </p>
                              
                              {item.product.price != null && (
                                <div className="flex items-center gap-2 mt-1">
                                  <span className="text-sm line-through text-gray-400">
                                    ${item.product.price.toFixed(2)}
                                  </span>
                                  <span className="text-sm font-medium text-red-600 dark:text-red-400">
                                    $0.00
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            <button
                              onClick={() => removeItem(user?.userId ?? userId, item.id)}
                              disabled={isUpdating}
                              className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1 disabled:opacity-50"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>

                          <div className="flex items-center justify-between mt-4">
                            <div className="flex items-center gap-3">
                              <button
                                onClick={() => handleQuantityChange(item.id, item.quantity, -1)}
                                disabled={isUpdating}
                                className="p-1 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                              >
                                <Minus size={14} />
                              </button>
                              
                              <span className="w-12 text-center text-sm font-medium text-gray-900 dark:text-white">
                                {item.quantity}
                              </span>
                              
                              <button
                                onClick={() => handleQuantityChange(item.id, item.quantity, 1)}
                                disabled={isUpdating}
                                className="p-1 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                              >
                                <Plus size={14} />
                              </button>
                            </div>
                            
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                                ${item.total.toFixed(2)}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                ${item.price.toFixed(2)} each
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>

            {/* Continue Shopping */}
            <div className="flex justify-center">
              <Link
                to="/products"
                className="inline-flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
              >
                <Package size={16} />
                Continue Shopping
              </Link>
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Order Summary
              </h3>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span className="text-gray-900 dark:text-white">${subtotal.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Estimated Tax</span>
                  <span className="text-gray-900 dark:text-white">${estimatedTax.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Delivery Fee</span>
                  <span className={"text-gray-900 dark:text-white"}>
                    {`$${deliveryFee.toFixed(2)}`}
                  </span>
                </div>
                
                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                  <div className="flex justify-between font-semibold text-lg">
                    <span className="text-gray-900 dark:text-white">Total</span>
                    <span className="text-gray-900 dark:text-white">${total.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Free Delivery Notice */}
              {deliveryFee > 0 && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Truck className="text-blue-600 dark:text-blue-400 mt-0.5" size={16} />
                    <div className="text-sm">
                      <p className="text-blue-800 dark:text-blue-200 font-medium">
                        Add ${(50 - subtotal).toFixed(2)} more for free delivery!
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Checkout Button */}
              <button
                onClick={handleCheckout}
                disabled={isUpdating || cart.items.length === 0}
                className="w-full mt-6 bg-indigo-600 text-white py-3 px-4 rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                Proceed to Checkout
                <ArrowRight size={16} />
              </button>

              {/* Security Notice */}
              <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <CheckCircle size={12} />
                <span>Secure checkout with 256-bit SSL encryption</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cart;