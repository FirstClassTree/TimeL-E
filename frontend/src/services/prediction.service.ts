import { api } from '@/services/api.client'; // REMOVED: mlApi import - use backend gateway only
import { Product } from '@/services/product.service';

export interface PredictedBasketItem {
  id: string;
  basketId: string;
  productId: string;
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
    productId: string;
    action: 'added' | 'removed' | 'quantity_changed';
    newQuantity?: number;
  }>;
  rating?: number;
  comment?: string;
}

class PredictionService {

  async getCurrentPredictedBasket(): Promise<PredictedBasket | null> {
    try {
      return await api.get<PredictedBasket>('/predictions/current-basket');
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
    itemId: string,
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
      productId: string;
      productName: string;
      reasons: string[];
      confidence: number;
    }>;
  }> {
    return api.get(`/predictions/baskets/${basketId}/explanation`);
  }
}

export const predictionService = new PredictionService();