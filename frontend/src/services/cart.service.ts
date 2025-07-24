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
    return this.transformBackendCart(response.data);
  }

  // Add item to cart
  async addToCart(userId: string, data: AddToCartData): Promise<Cart> {
    const requestData = {
      product_id: data.productId,
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
    return this.transformBackendCart(response.data);
  }

  // Transform backend cart response to frontend format
  private transformBackendCart(backendCart: any): Cart {
    if (!backendCart || !backendCart.items) {
      return {
        id: `cart_${Date.now()}`,
        userId: backendCart?.user_id || '',
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

    const transformedItems: CartItem[] = backendCart.items.map((item: any, index: number) => ({
      id: index + 1,
      cartId: `cart_${backendCart.user_id}`,
      productId: item.product_id,
      product: {
        product_id: item.product_id,
        product_name: item.product_name || 'Unknown Product',
        aisle_id: 0,
        department_id: 0,
        aisle_name: item.aisle_name || '',
        department_name: item.department_name || '',
        description: null,
        price: 0,
        image_url: null
      },
      quantity: item.quantity,
      price: 0, // Backend doesn't provide price, would need to fetch
      total: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }));

    const itemCount = transformedItems.reduce((sum, item) => sum + item.quantity, 0);
    const subtotal = transformedItems.reduce((sum, item) => sum + item.total, 0);

    return {
      id: `cart_${backendCart.user_id}`,
      userId: backendCart.user_id,
      items: transformedItems,
      itemCount: itemCount,
      subtotal: subtotal,
      estimatedTax: subtotal * 0.08,
      estimatedTotal: subtotal * 1.08,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
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
