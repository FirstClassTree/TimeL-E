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
  async getCart(userId: string): Promise<Cart> {
    return api.get<Cart>(`/cart/${userId}`);
  }

  // Add item to cart
  async addToCart(userId: string, data: AddToCartData): Promise<Cart> {
    return api.post<Cart>(`/cart/${userId}`, data);
  }

  // Update cart item
  async updateCartItem(userId : string, itemId: string, data: UpdateCartItemData): Promise<Cart> {
    return api.put<Cart>(`/cart/${userId}/items/${itemId}`, data);
  }

  // Remove item from cart
  async removeFromCart(userId : string, itemId: string): Promise<Cart> {
    return api.delete<Cart>(`/cart/${userId}/items/${itemId}`);
  }

  // Clear entire cart - Not supported in backend yet
  async clearCart(userId : string): Promise<Cart> {
    return api.post<Cart>(`/cart/${userId}/clear`);
  }

  // ============================================================================
  // ML INTEGRATION (Supporting core demands)
  // ============================================================================

  // Sync cart with predicted basket
  async syncWithPredictedBasket(userId : string, basketId: string): Promise<Cart> {
    return api.post<Cart>(`/cart/${userId}/sync-predicted/${basketId}`);
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

  // Supported in ml service? Get recommendations based on cart
  async getCartRecommendations(userId :string, limit: number = 4): Promise<Product[]> {
    return api.get<Product[]>(`/cart/${userId}/recommendations?limit=${limit}`);
  }
}

export const cartService = new CartService();