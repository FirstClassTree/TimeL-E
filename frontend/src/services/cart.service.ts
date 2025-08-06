import { dbApi } from '@/services/db.client';
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
    const response = await dbApi.get(`/cart/${userId}`);
    // DB Service returns direct response or wrapped response
    const cartData = response.data || response;
    return this.transformBackendCart(cartData);
  }

  // Add item to cart
  async addToCart(userId: string, data: AddToCartData): Promise<Cart> {
    console.log('CartService: addToCart called', { userId, data });
    const requestData = {
      productId: data.productId,
      quantity: data.quantity
    };
    console.log('CartService: Request data', requestData);
    const response = await dbApi.post(`/cart/${userId}/items`, requestData);
    console.log('CartService: API response', response);
    // DB Service returns direct response or wrapped response
    const cartData = response.data || response;
    console.log('CartService: Extracted cart data', cartData);
    const transformedCart = this.transformBackendCart(cartData);
    console.log('CartService: Transformed cart', transformedCart);
    return transformedCart;
  }

  // Update cart item
  async updateCartItem(userId: string, itemId: number, data: UpdateCartItemData): Promise<Cart> {
    const response = await dbApi.put(`/cart/${userId}/items/${itemId}`, data);
    // DB Service returns direct response or wrapped response
    const cartData = response.data || response;
    return this.transformBackendCart(cartData);
  }

  // Remove item from cart
  async removeFromCart(userId: string, itemId: number): Promise<Cart> {
    const response = await dbApi.delete(`/cart/${userId}/items/${itemId}`);
    // DB Service returns direct response or wrapped response
    const cartData = response.data || response;
    return this.transformBackendCart(cartData);
  }

  // Clear entire cart
  async clearCart(userId: string): Promise<Cart> {
    const response = await dbApi.delete(`/cart/${userId}/clear`);
    // DB Service returns direct response or wrapped response
    const cartData = response.data || response;
    return this.transformBackendCart(cartData);
  }

  // Transform backend cart response to frontend format
  private transformBackendCart(backendCart: any): Cart {
    if (!backendCart || !backendCart.items) {
      return {
        id: backendCart?.cartId || `cart_${Date.now()}`,
        userId: backendCart?.userId || '',
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
      cartId: backendCart.cartId,
      productId: item.productId,
      product: {
        productId: item.productId,
        productName: item.productName || 'Unknown Product',
        aisleId: 0,
        departmentId: 0,
        aisleName: item.aisleName || '',
        departmentName: item.departmentName || '',
        description: item.description || null,
        price: item.price || 0,
        imageUrl: item.imageUrl || null
      },
      quantity: item.quantity,
      price: item.price || 0,
      total: (item.price || 0) * item.quantity,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }));

    const itemCount = transformedItems.reduce((sum, item) => sum + item.quantity, 0);
    const subtotal = transformedItems.reduce((sum, item) => sum + item.total, 0);

    return {
      id: backendCart.cartId,
      userId: backendCart.userId,
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
    return dbApi.post<Cart>(`/cart/${userId}/sync-predicted/${basketId}`);
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
    return dbApi.get<Product[]>(`/cart/${userId}/recommendations?limit=${limit}`);
  }
}

export const cartService = new CartService();
