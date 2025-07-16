// frontend/src/services/cart.service.ts
// CLEANED: Removed coupon methods that backend doesn't support

import { api } from '@/services/api.client';
import { Product } from '@/services/product.service';

export interface CartItem {
  id: string;
  cartId: string;
  productId: string;
  product: Product;
  quantity: number;
  price: number;
  total: number;
  createdAt: string;
  updatedAt: string;
}

export interface Cart {
  id: string;
  userId: string;
  items: CartItem[];
  itemCount: number;
  subtotal: number;
  estimatedTax: number;
  estimatedTotal: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AddToCartData {
  productId: string;
  quantity: number;
}

export interface UpdateCartItemData {
  quantity: number;
}

class CartService {
  
  // ============================================================================
  // CORE CART OPERATIONS (Essential functionality)
  // ============================================================================

  // Get current cart
  async getCart(): Promise<Cart> {
    return api.get<Cart>('/cart');
  }

  // Add item to cart
  async addToCart(data: AddToCartData): Promise<Cart> {
    return api.post<Cart>('/cart/add', data);
  }

  // Update cart item quantity
  async updateCartItem(itemId: string, data: UpdateCartItemData): Promise<Cart> {
    return api.put<Cart>(`/cart/items/${itemId}`, data);
  }

  // Remove item from cart
  async removeFromCart(itemId: string): Promise<Cart> {
    return api.delete<Cart>(`/cart/items/${itemId}`);
  }

  // Clear entire cart
  async clearCart(): Promise<Cart> {
    return api.post<Cart>('/cart/clear');
  }

  // ============================================================================
  // ML INTEGRATION (Supporting core demands)
  // ============================================================================

  // Sync cart with predicted basket
  async syncWithPredictedBasket(basketId: string): Promise<Cart> {
    return api.post<Cart>(`/cart/sync-predicted/${basketId}`);
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  // Get cart count (for header badge)
  async getCartCount(): Promise<number> {
    try {
      const cart = await this.getCart();
      return cart.itemCount;
    } catch {
      return 0;
    }
  }

  // Check if product is in cart
  isProductInCart(cart: Cart, productId: string): boolean {
    return cart.items.some(item => item.productId === productId);
  }

  // Get cart item by product ID
  getCartItem(cart: Cart, productId: string): CartItem | undefined {
    return cart.items.find(item => item.productId === productId);
  }

  // Calculate cart totals
  calculateTotals(cart: Cart): {
    subtotal: number;
    itemCount: number;
    savings: number;
  } {
    const subtotal = cart.items.reduce((sum, item) => sum + item.total, 0);
    const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    
    // Calculate savings from sale prices
    const savings = cart.items.reduce((sum, item) => {
      if (item.product.compareAtPrice && item.product.compareAtPrice > item.product.price) {
        const itemSavings = (item.product.compareAtPrice - item.product.price) * item.quantity;
        return sum + itemSavings;
      }
      return sum;
    }, 0);

    return { subtotal, itemCount, savings };
  }

  // Validate cart items (check stock, prices)
  async validateCart(): Promise<{
    isValid: boolean;
    issues: Array<{
      itemId: string;
      productId: string;
      issue: string;
      suggestion: string;
    }>;
  }> {
    return api.post('/cart/validate');
  }

  // Estimate shipping costs
  async estimateShipping(zipCode: string, country?: string): Promise<{
    cost: number;
    estimatedDays: number;
    method: string;
  }> {
    return api.post('/cart/estimate-shipping', { zipCode, country });
  }

  // Get cart-based recommendations
  async getCartRecommendations(limit: number = 4): Promise<Product[]> {
    return api.get<Product[]>(`/cart/recommendations?limit=${limit}`);
  }
}

export const cartService = new CartService();

// ============================================================================
// REMOVED DEAD CODE:
// 
// DELETED COUPON METHODS:
// - applyCoupon(code: string): Promise<Cart>
// - removeCoupon(): Promise<Cart>
//
// REASON FOR REMOVAL:
// The backend cart routes and controller don't implement coupon functionality.
// These methods would result in 404 errors when called. Coupon systems are
// complex features not required for the dev/test stage focused on core ML
// demonstration.
//
// ALIGNMENT WITH BACKEND:
// This service now perfectly aligns with the backend's cart API, providing
// all necessary functionality for:
// - Demand 1: Cart management for seeded users
// - Demand 4: Good shopping user experience and cart operations
// 
// The service maintains all essential cart functionality while eliminating
// dead endpoints that would cause runtime errors.
// ============================================================================