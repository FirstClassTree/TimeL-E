import { api } from '@/services/api.client';
import { Product } from '@/services/product.service';

export interface OrderItem {
  id: string;
  orderId: string;
  productId: string;
  product: Product;
  quantity: number;
  price: number;
  total: number;
  createdAt: string;
}

export interface Delivery {
  id: string;
  orderId: string;
  type: 'standard' | 'express' | 'scheduled';
  status: 'pending' | 'scheduled' | 'in_transit' | 'delivered' | 'failed';
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  scheduledDate?: string;
  scheduledTimeStart?: string;
  scheduledTimeEnd?: string;
  deliveredAt?: string;
  deliveryNotes?: string;
  trackingNumber?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  items: OrderItem[];
  delivery?: Delivery;
  subtotal: number;
  tax: number;
  deliveryFee: number;
  discount: number;
  total: number;
  paymentMethod: string;
  paymentStatus: string;
  notes?: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface CreateOrderData {
  cartId: string;
  deliveryAddress: {
    street: string;
    city: string;
    state: string;
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
  totalPages: number;
  hasMore: boolean;
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
    return api.post<Order>('/orders/create', data);
  }

  // Get all orders for the current user
  async getOrders(filters: OrderFilters = {}): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.startDate) params.append('startDate', filters.startDate);
    if (filters.endDate) params.append('endDate', filters.endDate);
    if (filters.sort) params.append('sort', filters.sort);

    return api.get<OrdersResponse>(`/orders?${params.toString()}`);
  }

  // Get a single order by ID
  async getOrder(orderId: string): Promise<Order> {
    return api.get<Order>(`/orders/${orderId}`);
  }

  async getOrderItems(orderId: string): Promise<Order> {
    return api.get<Order>(`/orders/${orderId}/items`);
  }

    async addItemsToOrder(orderId: string): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/items`);
  }

  // Cancel an order
  async cancelOrder(orderId: string, reason?: string): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/cancel`, { reason });
  }

  // Request refund
  async requestRefund(orderId: string, reason: string, items?: string[]): Promise<Order> {
    return api.post<Order>(`/orders/${orderId}/refund`, { reason, items });
  }

  // Reorder items from a previous order
  async reorder(orderId: string): Promise<{ cartId: string }> {
    return api.post<{ cartId: string }>(`/orders/${orderId}/reorder`);
  }

  // Get order tracking information
  async getTracking(orderId: string): Promise<TrackingInfo> {
    return api.get<TrackingInfo>(`/orders/${orderId}/tracking`);
  }

  // Download order invoice
  async downloadInvoice(orderId: string): Promise<Blob> {
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
  async updateDeliveryInstructions(orderId: string, instructions: string): Promise<Order> {
    return api.put<Order>(`/orders/${orderId}/delivery-instructions`, { instructions });
  }

  // Rate order
  async rateOrder(orderId: string, rating: number, comment?: string): Promise<void> {
    return api.post(`/orders/${orderId}/rate`, { rating, comment });
  }

  // Get recommended products based on order history
  async getRecommendedProducts(limit: number = 10): Promise<Product[]> {
    return api.get<Product[]>(`/orders/recommendations?limit=${limit}`);
  }

  // Admin functions
  async getAllOrders(filters: OrderFilters & { userId?: string } = {}): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    return api.get<OrdersResponse>(`/admin/orders?${params.toString()}`);
  }

  async updateOrderStatus(orderId: string, update: OrderStatusUpdate): Promise<Order> {
    return api.put<Order>(`/admin/orders/${orderId}/status`, update);
  }

  async updateTracking(orderId: string, trackingNumber: string, carrier: string): Promise<Order> {
    return api.put<Order>(`/admin/orders/${orderId}/tracking`, { trackingNumber, carrier });
  }

  // Utility functions
  getStatusColor(status: Order['status']): string {
    const colors = {
      pending: 'yellow',
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
      pending: 'clock',
      processing: 'loader',
      shipped: 'truck',
      delivered: 'check-circle',
      cancelled: 'x-circle',
      returned: 'rotate-ccw'
    };
    return icons[status] || 'package';
  }

  formatOrderNumber(orderNumber: string): string {
    return `#${orderNumber.toUpperCase()}`;
  }

  canCancel(order: Order): boolean {
    return ['pending', 'processing'].includes(order.status);
  }

  canRequestRefund(order: Order): boolean {
    return order.status === 'delivered' && 
           new Date(order.createdAt).getTime() > Date.now() - 30 * 24 * 60 * 60 * 1000; // 30 days
  }
}

export const orderService = new OrderService();