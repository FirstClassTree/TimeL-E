import { api } from '@/services/api.client';
import { Product } from '@/services/product.service';

export interface CartItem {
  id: number;
  cartId: string;
  productId: number;
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
  productId: number;
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
    const response = await api.get(`/cart/${userId}`);
    return this.transformBackendCart(response);
  }

  // Add item to cart
  async addToCart(userId: string, data: AddToCartData): Promise<Cart> {
    const requestData = {
      productId: data.productId,
      quantity: data.quantity
    };
    const response = await api.post(`/cart/${userId}/items`, requestData);
    // After adding item, fetch updated cart
    return this.getCart(userId);
  }

  // Update cart item
  async updateCartItem(userId: string, itemId: number, data: UpdateCartItemData): Promise<Cart> {
    const response = await api.put(`/cart/${userId}/items/${itemId}`, data);
    // After updating, fetch updated cart
    return this.getCart(userId);
  }

  // Remove item from cart
  async removeFromCart(userId: string, itemId: number): Promise<Cart> {
    const response = await api.delete(`/cart/${userId}/items/${itemId}`);
    // After removing, fetch updated cart
    return this.getCart(userId);
  }

  // Clear entire cart
  async clearCart(userId: string): Promise<Cart> {
    const response = await api.delete(`/cart/${userId}`);
    return this.transformBackendCart(response);
  }

  // Transform backend cart response to frontend format
  private transformBackendCart(backendCart: any): Cart {
    console.log('[CartService] transformBackendCart input:', JSON.stringify(backendCart, null, 2));
    
    try {
      // Handle null, undefined, or malformed cart responses
      if (!backendCart || typeof backendCart !== 'object') {
        console.log('[CartService] Empty/invalid cart response, returning empty cart');
        return {
          id: `empty_cart_${Date.now()}`,
          userId: '',
          items: [],
          itemCount: 0,
          subtotal: 0,
          estimatedTax: 0,
          estimatedTotal: 0,
          isActive: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
      }

      // Handle empty cart or cart with no items
      if (!backendCart.items || !Array.isArray(backendCart.items) || backendCart.items.length === 0) {
        console.log('[CartService] No items in cart, returning empty cart');
        return {
          id: backendCart.cartId || backendCart.cart_id || `empty_cart_${backendCart.userId || Date.now()}`,
          userId: backendCart.userId || '',
          items: [],
          itemCount: 0,
          subtotal: 0,
          estimatedTax: 0,
          estimatedTotal: 0,
          isActive: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
      }

      console.log('[CartService] Processing cart items:', backendCart.items.length);

      const transformedItems: CartItem[] = backendCart.items.map((item: any, index: number) => {
        console.log(`[CartService] Transforming item ${index}:`, JSON.stringify(item, null, 2));
        
        const transformedItem = {
          id: index + 1,
          cartId: `cart_${backendCart.userId}`,
          productId: item.productId,
          product: {
            productId: item.productId,
            productName: item.productName || 'Unknown Product',
            aisleId: null,
            departmentId: null,
            aisleName: item.aisleName || '',
            departmentName: item.departmentName || '',
            description: item.description || null,
            price: item.price || null,
            imageUrl: item.imageUrl || null
          },
          quantity: item.quantity,
          price: item.price || 0,
          total: (item.price || 0) * item.quantity,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };

        console.log(`[CartService] Transformed item ${index}:`, JSON.stringify(transformedItem, null, 2));
        return transformedItem;
      });

      const itemCount = transformedItems.reduce((sum, item) => sum + item.quantity, 0);
      const subtotal = transformedItems.reduce((sum, item) => sum + item.total, 0);

      const finalCart = {
        id: backendCart.cartId || backendCart.cart_id || `cart_${backendCart.userId}`,
        userId: backendCart.userId,
        items: transformedItems,
        itemCount: backendCart.totalItems || backendCart.total_items || itemCount,
        subtotal: subtotal,
        estimatedTax: subtotal * 0.08,
        estimatedTotal: subtotal * 1.08,
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      console.log('[CartService] Final transformed cart:', JSON.stringify(finalCart, null, 2));
      return finalCart;

    } catch (error: any) {
      console.error('[CartService] Error in transformBackendCart:', error);
      console.error('[CartService] Stack trace:', error.stack);
      throw error;
    }
  }

  // ============================================================================
  // ML INTEGRATION (Supporting core demands)
  // ============================================================================

  // Sync cart with predicted basket
  async syncWithPredictedBasket(userId : string, basketId: string): Promise<Cart> {
    return api.post<Cart>(`/cart/${userId}/sync-predicted/${basketId}`);
  }

  // Check if product is in cart
  isProductInCart(cart: Cart, productId: number): boolean {
    return cart.items.some(item => item.productId === productId);
  }

  // Get cart item by product ID
  getCartItem(cart: Cart, productId: number): CartItem | undefined {
    return cart.items.find(item => item.productId === productId);
  }

  // Calculate cart totals
  calculateTotals(cart: Cart): {
    subtotal: number;
    itemCount: number;
  } {
    const subtotal = cart.items.reduce((sum, item) => sum + item.total, 0);
    const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);

    return { subtotal, itemCount };
  }

  // Supported in ml service? Get recommendations based on cart
  async getCartRecommendations(userId :string, limit: number = 4): Promise<Product[]> {
    return api.get<Product[]>(`/cart/${userId}/recommendations?limit=${limit}`);
  }
}

export const cartService = new CartService();
