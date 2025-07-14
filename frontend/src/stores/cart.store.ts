// frontend/src/stores/cart.store.ts
// FIXED: Removed window.confirm from store to properly separate concerns
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { cartService, Cart, CartItem } from '@/services/cart.service';
import { Product } from '@/services/product.service';
import toast from 'react-hot-toast';

interface CartState {
  cart: Cart | null;
  isLoading: boolean;
  isUpdating: boolean;
  
  // Actions
  fetchCart: () => Promise<void>;
  addToCart: (productId: string, quantity?: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  syncWithPredictedBasket: (basketId: string) => Promise<void>;
  
  // Computed values
  getItemCount: () => number;
  getSubtotal: () => number;
  getSavings: () => number;
  isProductInCart: (productId: string) => boolean;
  getCartItem: (productId: string) => CartItem | undefined;
}

export const useCartStore = create<CartState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      cart: null,
      isLoading: false,
      isUpdating: false,

      fetchCart: async () => {
        set({ isLoading: true });
        try {
          const cart = await cartService.getCart();
          set({ cart, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          console.error('Failed to fetch cart:', error);
        }
      },

      addToCart: async (productId, quantity = 1) => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.addToCart({ productId, quantity });
          set({ cart, isUpdating: false });
          
          const addedItem = cart.items.find(item => item.productId === productId);
          if (addedItem) {
            toast.success(`${addedItem.product.name} added to cart`);
          }
        } catch (error: any) {
          set({ isUpdating: false });
          if (error.response?.status !== 401) {
            toast.error('Failed to add item to cart');
          }
          throw error;
        }
      },

      updateQuantity: async (itemId, quantity) => {
        if (quantity < 1) {
          return get().removeItem(itemId);
        }

        set({ isUpdating: true });
        try {
          const cart = await cartService.updateCartItem(itemId, { quantity });
          set({ cart, isUpdating: false });
        } catch (error) {
          set({ isUpdating: false });
          toast.error('Failed to update quantity');
          throw error;
        }
      },

      removeItem: async (itemId) => {
        set({ isUpdating: true });
        
        // Optimistically update UI
        const currentCart = get().cart;
        if (currentCart) {
          const removedItem = currentCart.items.find(item => item.id === itemId);
          const updatedItems = currentCart.items.filter(item => item.id !== itemId);
          const updatedCart = {
            ...currentCart,
            items: updatedItems,
            itemCount: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            subtotal: updatedItems.reduce((sum, item) => sum + (item.price * item.quantity), 0)
          };
          set({ cart: updatedCart });

          if (removedItem) {
            toast.success(`${removedItem.product.name} removed from cart`);
          }
        }

        try {
          const cart = await cartService.removeFromCart(itemId);
          set({ cart, isUpdating: false });
        } catch (error) {
          // Revert optimistic update on error
          if (currentCart) {
            set({ cart: currentCart });
          }
          set({ isUpdating: false });
          toast.error('Failed to remove item');
          throw error;
        }
      },

      // FIXED: Removed window.confirm from store - UI logic moved to component
      clearCart: async () => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.clearCart();
          set({ cart, isUpdating: false });
          toast.success('Cart cleared');
        } catch (error) {
          set({ isUpdating: false });
          toast.error('Failed to clear cart');
          throw error;
        }
      },

      syncWithPredictedBasket: async (basketId) => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.syncWithPredictedBasket(basketId);
          set({ cart, isUpdating: false });
          toast.success('Cart updated with predicted items');
        } catch (error) {
          set({ isUpdating: false });
          toast.error('Failed to sync with predicted basket');
          throw error;
        }
      },

      // Computed values
      getItemCount: () => {
        const { cart } = get();
        return cart?.itemCount || 0;
      },

      getSubtotal: () => {
        const { cart } = get();
        return cart?.subtotal || 0;
      },

      getSavings: () => {
        const { cart } = get();
        if (!cart) return 0;
        return cartService.calculateSavings(cart);
      },

      isProductInCart: (productId) => {
        const { cart } = get();
        if (!cart) return false;
        return cartService.isProductInCart(cart, productId);
      },

      getCartItem: (productId) => {
        const { cart } = get();
        if (!cart) return undefined;
        return cartService.getCartItem(cart, productId);
      }
    })),
    {
      name: 'cart-store'
    }
  )
);

// Auto-fetch cart on auth state change
useCartStore.subscribe(
  (state) => state.cart,
  (cart) => {
    // Update cart badge in UI
    const event = new CustomEvent('cart-updated', { detail: { itemCount: cart?.itemCount || 0 } });
    window.dispatchEvent(event);
  }
);