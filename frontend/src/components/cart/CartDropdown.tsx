import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingCart, Trash2, Plus, Minus, X } from 'lucide-react';
import { useCartStore } from '@/stores/cart.store';
import { useAuthStore } from '@/stores/auth.store';

interface CartDropdownProps {
  onClose: () => void;
}

const CartDropdown: React.FC<CartDropdownProps> = ({ onClose }) => {
  const { cart, updateQuantity, removeItem, getSubtotal, getItemCount } = useCartStore();
    const { user } = useAuthStore();

  const handleQuantityChange = async (productId: number, currentQuantity: number, delta: number) => {
    if (!user?.userId) return;

    const newQuantity = currentQuantity + delta;
    if (newQuantity < 1) {
      await removeItem(user.userId, productId);
    } else {
      await updateQuantity(user.userId, productId, newQuantity);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
      />
      
      {/* Dropdown */}
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Shopping Cart
            </h3>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X size={20} />
            </button>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {getItemCount()} {getItemCount() === 1 ? 'item' : 'items'}
          </p>
        </div>

        {/* Cart Items */}
        <div className="max-h-96 overflow-y-auto">
          {!cart || cart.items.length === 0 ? (
            <div className="p-6 text-center">
              <ShoppingCart className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Your cart is empty
              </p>
              <Link
                to="/products"
                onClick={onClose}
                className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Start Shopping
              </Link>
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {cart.items.map((item) => (
                <div key={item.id} className="flex items-center gap-3">
                  {/* Product Image */}
                  <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                    <img
                      src={item.product.imageUrl}
                      alt={item.product.productName}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>

                  {/* Product Info */}
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {item.product.productName}
                    </h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      ${item.price.toFixed(2)}
                    </p>
                  </div>

                  {/* Quantity Controls */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleQuantityChange(item.id, item.quantity, -1)}
                      className="w-6 h-6 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <Minus size={12} />
                    </button>
                    
                    <span className="w-8 text-center text-sm font-medium text-gray-900 dark:text-white">
                      {item.quantity}
                    </span>
                    
                    <button
                      onClick={() => handleQuantityChange(item.id, item.quantity, 1)}
                      className="w-6 h-6 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <Plus size={12} />
                    </button>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => removeItem(user.id, item.id)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {cart && cart.items.length > 0 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Total:
              </span>
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                ${getSubtotal().toFixed(2)}
              </span>
            </div>
            
            <div className="space-y-2">
              <Link
                to="/cart"
                onClick={onClose}
                className="block w-full text-center bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white py-2 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                View Cart
              </Link>
              <Link
                to="/checkout"
                onClick={onClose}
                className="block w-full text-center bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Checkout
              </Link>
            </div>
          </div>
        )}
      </motion.div>
    </>
  );
};

export default CartDropdown;