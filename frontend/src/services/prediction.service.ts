import { api } from '@/services/api.client'; // REMOVED: mlApi import - use backend gateway only
import { Product } from '@/services/product.service';

export interface PredictedBasketItem {
  id: string;
  basketId: string;
  productId: number;
  product: Product;
  quantity: number;
  confidenceScore: number;
  isAccepted: boolean;
  reason?: string;
  createdAt: string;
}

export interface PredictedBasket {
  id: string;
  userId: string;
  weekOf: string;
  status: 'generated' | 'modified' | 'accepted' | 'rejected';
  confidenceScore: number;
  items: PredictedBasketItem[];
  totalItems: number;
  totalValue: number;
  acceptedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ModelMetrics {
  precisionAt10: number;
  recallAt10: number;
  hitRate: number;
  ndcg: number;
  f1Score: number;
  lastUpdated: string;
}

export interface OnlineMetrics {
  autoCartAcceptanceRate: number;
  avgEditDistance: number;
  cartValueUplift: number;
  userSatisfactionScore: number;
  totalPredictions: number;
  successfulPredictions: number;
}

export interface PredictionFeedback {
  basketId: string;
  accepted: boolean;
  modifiedItems?: Array<{
    productId: number;
    action: 'added' | 'removed' | 'quantity_changed';
    newQuantity?: number;
  }>;
  rating?: number;
  comment?: string;
}

class PredictionService {

  async getCurrentPredictedBasket(userId?: string): Promise<PredictedBasket | null> {
    try {
      if (!userId) {
        // Try to get user ID from auth store
        const authStore = (await import('@/stores/auth.store')).useAuthStore;
        const user = authStore.getState().user;
        if (!user?.userId) {
          return null;
        }
        userId = user.userId;
      }

      // Call the actual backend endpoint
      const response = await api.get(`/predictions/user/${userId}`);
      
      // Transform the backend response to frontend format
      if (response.predictions && response.predictions.length > 0) {
        const mockBasket: PredictedBasket = {
          id: `basket_${userId}_${Date.now()}`,
          userId: response.userId,
          weekOf: new Date().toISOString(),
          status: 'generated',
          confidenceScore: 0.8,
          items: response.predictions.map((pred: any, index: number) => ({
            id: `item_${pred.productId}_${index}`,
            basketId: `basket_${userId}_${Date.now()}`,
            productId: pred.productId,
            product: {
              productId: pred.productId,
              productName: pred.productName,
              aisleId: 1,
              departmentId: 1,
              aisleName: 'Unknown Aisle',
              departmentName: 'Unknown Department',
              price: Math.random() * 10 + 2, // Mock price
              imageUrl: '/storage/image_not_available.png'
            },
            quantity: 1,
            confidenceScore: pred.score,
            isAccepted: true,
            createdAt: new Date().toISOString()
          })),
          totalItems: response.predictions.length,
          totalValue: response.predictions.length * 5, // Mock total
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        
        return mockBasket;
      }
      
      return null;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get all predicted baskets for user
   */
  async getUserPredictedBaskets(userId : string): Promise<{
    baskets: PredictedBasket[];
    total: number;
    page: number;
    totalPages: number;
  }> {
    return api.get(`/predictions/user/${userId}`);
  }

  /**
   * Generate new prediction via backend
   */
  async generatePrediction(options?: {
    weekOf?: string;
    forceRegenerate?: boolean;
  }): Promise<PredictedBasket> {
    return api.post<PredictedBasket>('/predictions/generate', options);
  }

  /**
   * Update predicted basket item
   */
  async updateBasketItem(
    basketId: string,
    itemId: number,
    data: {
      quantity?: number;
      isAccepted?: boolean;
      reason?: string;
    }
  ): Promise<PredictedBasket> {
    return api.put<PredictedBasket>(`/predictions/baskets/${basketId}/items/${itemId}`, data);
  }

  /**
   * Accept/reject predicted basket
   */
  async updateBasketStatus(
    basketId: string,
    status: 'accepted' | 'rejected',
    feedback?: PredictionFeedback
  ): Promise<PredictedBasket> {
    return api.put<PredictedBasket>(`/predictions/baskets/${basketId}/status`, {
      status,
      feedback
    });
  }

  /**
   * Submit prediction feedback
   */
  async submitFeedback(feedback: PredictionFeedback): Promise<void> {
    return api.post('/predictions/feedback', feedback);
  }

  // ============================================================================
  // MODEL METRICS - Via Backend Gateway
  // ============================================================================

  /**
   * Get model performance metrics via backend
   */
  async getModelMetrics(): Promise<ModelMetrics> {
    return api.get<ModelMetrics>('/predictions/metrics/model-performance');
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Check if user has pending predictions
   */
  async hasPendingPredictions(): Promise<boolean> {
    try {
      const current = await this.getCurrentPredictedBasket();
      return current !== null && current.status === 'generated';
    } catch {
      return false;
    }
  }

  /**
   * Get prediction explanation
   */
  async getPredictionExplanation(basketId: string): Promise<{
    overallConfidence: number;
    explanations: Array<{
      productId: number;
      productName: string;
      reasons: string[];
      confidence: number;
    }>;
  }> {
    return api.get(`/predictions/baskets/${basketId}/explanation`);
  }
}

export const predictionService = new PredictionService();
