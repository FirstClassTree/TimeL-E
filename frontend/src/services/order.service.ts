import { api } from '@/services/api.client';
import { Product } from '@/services/product.service';

export interface OrderItem {
    id: string;
    name: string;
    price: number;
    quantity: number;
    image: string;
    category: string;
}

export interface Order {
  orderId: number;
  orderNumber: number;
  userId: string;
  status: 'PENDING' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  items: OrderItem[];
  total: number;
  createdAt: string;
}

export interface CreateOrderData {
  cartId: string;
  deliveryAddress: {
    street: string;
    city: string;
    zipCode: string;
    country: string;
  };
  paymentMethod: string;
  notes?: string;
}

export interface OrdersResponse {
  orders: Order[];
  total: number;
  page: number;
  perPage: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface OrderFilters {
  page?: number;
  limit?: number;
  status?: string;
  startDate?: string;
  endDate?: string;
  sort?: string;
}

export interface OrderStatusUpdate {
  status: Order['status'];
  reason?: string;
}

export interface TrackingInfo {
  carrier: string;
  trackingNumber: string;
  estimatedDelivery: string;
  currentLocation?: string;
  events: Array<{
    date: string;
    location: string;
    status: string;
    description: string;
  }>;
}

class OrderService {

  async createOrder(data: CreateOrderData): Promise<Order> {
    return api.post<Order>('/orders', data);
  }

  // Get all orders for the current user
  async getOrders(userId: string, filters: OrderFilters = {}): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.startDate) params.append('startDate', filters.startDate);
    if (filters.endDate) params.append('endDate', filters.endDate);
    if (filters.sort) params.append('sort', filters.sort);

    return await api.get<OrdersResponse>(`/orders/user/${userId}?${params.toString()}`);
  }

  // Get order by ID
  async getOrder(orderId: number): Promise<Order> {
    return api.get<Order>(`/orders/${orderId}`);
  }

  async getOrderItems(orderId: number): Promise<Order> {
    return api.get<Order>(`/orders/${orderId}/items`);
  }

    async addItemsToOrder(orderId: number): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/items`);
  }

  // Cancel an order
  async cancelOrder(orderId: number, reason?: string): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/cancel`, { reason });
  }

  // Request refund
  async requestRefund(orderId: number, reason: string, items?: string[]): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/refund`, { reason, items });
  }

  // Reorder items from a previous order
  async reorder(orderId: number): Promise<{ cartId: string }> {
    return api.post<{ cartId: string }>(`/orders/${orderId}/reorder`);
  }

  // Get order tracking information
  async getTracking(orderId: number): Promise<TrackingInfo> {
    return api.get<TrackingInfo>(`/orders/${orderId}/tracking`);
  }

  // Download order invoice
  async downloadInvoice(orderId: number): Promise<Blob> {
    const response = await api.get(`/orders/${orderId}/invoice`, {
      responseType: 'blob'
    });
    return response as Blob;
  }

  // Get order statistics
  async getOrderStats(): Promise<{
    totalOrders: number;
    totalSpent: number;
    averageOrderValue: number;
    favoriteProducts: Array<{ product: Product; count: number }>;
    orderFrequency: string;
  }> {
    return api.get('/orders/stats');
  }

  // Update delivery instructions
  async updateDeliveryInstructions(orderId: number, instructions: string): Promise<Order> {
    return api.put<Order>(`/orders/${orderId}/delivery-instructions`, { instructions });
  }

  // Rate order
  async rateOrder(orderId: number, rating: number, comment?: string): Promise<void> {
    return api.post(`/orders/${orderId}/rate`, { rating, comment });
  }

  // Get recommended products based on order history
  async getRecommendedProducts(limit: number = 10): Promise<Product[]> {
    return api.get<Product[]>(`/orders/recommendations?limit=${limit}`);
  }

  async getAllOrders(filters: OrderFilters & { userId?: string } = {}): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    return api.get<OrdersResponse>(`/admin/orders?${params.toString()}`);
  }

  async updateOrderStatus(orderId: number, update: OrderStatusUpdate): Promise<Order> {
    return api.put<Order>(`/admin/orders/${orderId}/status`, update);
  }

  // Utility functions
  getStatusColor(status: Order['status']): string {
    const colors = {
      PENDING: 'yellow',
      processing: 'blue',
      shipped: 'indigo',
      delivered: 'green',
      cancelled: 'gray',
      returned: 'red'
    };
    return colors[status] || 'gray';
  }

  getStatusIcon(status: Order['status']): string {
    const icons = {
      PENDING: 'clock',
      processing: 'loader',
      shipped: 'truck',
      delivered: 'check-circle',
      cancelled: 'x-circle',
      returned: 'rotate-ccw'
    };
    return icons[status] || 'package';
  }

  canCancel(order: Order): boolean {
    return ['PENDING', 'processing'].includes(order.status);
  }

  canRequestRefund(order: Order): boolean {
    return order.status === 'delivered' && 
           new Date(order.createdAt).getTime() > Date.now() - 30 * 24 * 60 * 60 * 1000; // 30 days
  }
}

export const orderService = new OrderService();