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
  fetchCart: (userId: string) => Promise<void>;
  addToCart: (userId: string, productId: number, quantity?: number) => Promise<void>;
  updateQuantity: (userId: string, itemId: number, quantity: number) => Promise<void>;
  removeItem: (userId: string, itemId: number) => Promise<void>;
  clearCart: (userId: string) => Promise<void>;
  syncWithPredictedBasket: (userId: string, basketId: string) => Promise<void>;

  // Computed values
  getItemCount: () => number;
  getSubtotal: () => number;
  isProductInCart: (productId: number) => boolean;
  getCartItem: (userId: string, productId: number) => CartItem | undefined;
}

export const useCartStore = create<CartState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      cart: null,
      isLoading: false,
      isUpdating: false,

      fetchCart: async (userId: string) => {
        set({ isLoading: true });
        try {
          const cart = await cartService.getCart(userId);
          set({ cart, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          console.error('Failed to fetch cart:', error);
        }
      },

      addToCart: async (userId: string, productId: number, quantity = 1) => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.addToCart(userId, { productId, quantity });
          set({ cart, isUpdating: false });

          const addedItem = cart.items.find(item => item.productId === productId);
          if (addedItem) {
            toast.success(`${addedItem.product.product_name} added to cart`);
          }
        } catch (error: any) {
          set({ isUpdating: false });
          if (error.response?.status !== 401) {
            toast.error('Failed to add item to cart');
          }
          throw error;
        }
      },

      updateQuantity: async (userId: string, productId: number, quantity: number) => {
        if (quantity < 1) {
          return get().removeItem(userId, productId);
        }

        set({ isUpdating: true });
        try {
          const cart = await cartService.updateCartItem(userId, productId, { quantity });
          set({ cart, isUpdating: false });
        } catch (error) {
          set({ isUpdating: false });
          toast.error('Failed to update quantity');
          throw error;
        }
      },

      removeItem: async (userId: string, productId: number) => {
        set({ isUpdating: true });

        // Optimistically update UI
        const currentCart = get().cart;
        if (currentCart) {
          const removedItem = currentCart.items.find(item => item.productId === productId);
          const updatedItems = currentCart.items.filter(item => item.productId !== productId);
          const updatedCart = {
            ...currentCart,
            items: updatedItems,
            itemCount: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            subtotal: updatedItems.reduce((sum, item) => sum + (item.price * item.quantity), 0)
          };
          set({ cart: updatedCart });

          if (removedItem) {
            toast.success(`${removedItem.product.product_name} removed from cart`);
          }
        }

        try {
          const cart = await cartService.removeFromCart(userId, productId);
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

      clearCart: async (userId: string) => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.clearCart(userId);
          set({ cart, isUpdating: false });
          toast.success('Cart cleared');
        } catch (error) {
          set({ isUpdating: false });
          toast.error('Failed to clear cart');
          throw error;
        }
      },

      syncWithPredictedBasket: async (userId: string, basketId: string) => {
        set({ isUpdating: true });
        try {
          const cart = await cartService.syncWithPredictedBasket(userId, basketId);
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

      isProductInCart: (productId: number) => {
        const { cart } = get();
        if (!cart) return false;
        return cartService.isProductInCart(cart, productId);
      },

      getCartItem: (userId: string, productId: number) => {
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
