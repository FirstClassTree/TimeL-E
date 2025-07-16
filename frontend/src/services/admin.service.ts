// frontend/src/services/admin.service.ts
// FIXED: Added data transformation function for snake_case to camelCase conversion

import { api } from '@/services/api.client';

export interface ModelMetrics {
  precisionAt10: number;
  recallAt10: number;
  hitRate: number;
  ndcg: number;
  f1Score: number;
  evaluationTime?: string;
  sampleSize?: number;
}

export interface SystemHealth {
  status: string;
  database: string;
  mlService: string;
  timestamp: string;
}

export interface DashboardStats {
  totalUsers: number;
  totalProducts: number;
  totalOrders: number;
  totalRevenue: number;
  averageOrderValue: number;
  topCategories: Array<{
    name: string;
    count: number;
  }>;
  recentOrders: Array<{
    id: string;
    user: string;
    total: number;
    createdAt: string;
  }>;
  monthlyRevenue: Array<{
    month: string;
    revenue: number;
  }>;
}

export interface DemoUserPrediction {
  userId: string;
  predictedBasket: Array<{ id: string; name: string; imageUrl?: string; price: number; category?: string; }>;
  trueFutureBasket: Array<{ id: string; name: string; imageUrl?: string; price: number; category?: string; }>;
  comparisonMetrics: { predictedCount: number; actualCount: number; commonItems: number; };
}

// FIXED: Updated interface to reflect new backend response
export interface DemoUserIds {
  message: string;
  note: string;
  feature_engineering: string;
  restriction: string;
}

class AdminService {
  
  // ============================================================================
  // PRIVATE UTILITY METHODS
  // ============================================================================
  
  /**
   * FIXED: Transform snake_case ML service response to camelCase for frontend
   * This ensures consistency in the UI components
   */
  private transformEvaluationMetrics(data: any): ModelMetrics {
    return {
      precisionAt10: data.precision_at_k?.['10'] || data.precision_at_10 || 0,
      recallAt10: data.recall_at_k?.['10'] || data.recall_at_10 || 0,
      hitRate: data.hit_rate || data.hitRate || 0,
      ndcg: data.ndcg || data.NDCG || 0,
      f1Score: data.f1_score || data.f1Score || 0,
      evaluationTime: data.timestamp || new Date().toISOString(),
      sampleSize: data.sample_size || data.sampleSize || 100
    };
  }

  /**
   * Transform array of metrics if needed
   */
  private transformMetricsArray(data: any[]): ModelMetrics[] {
    return data.map(item => this.transformEvaluationMetrics(item));
  }
  
  // ============================================================================
  // SYSTEM MONITORING & EVALUATION
  // ============================================================================
  
  async getDashboardStats(): Promise<DashboardStats> {
    return api.get('/admin/dashboard/stats');
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return api.get('/admin/system/health');
  }

  /**
   * DEMAND 2: Trigger model evaluation
   * FIXED: Now properly transforms the response data
   */
  async triggerModelEvaluation(sampleSize?: number): Promise<ModelMetrics> {
    const response = await api.post('/admin/ml/evaluate', { sampleSize });
    
    // Extract metrics from various possible response structures
    const rawMetrics = response.results?.metrics || response.metrics || response;
    
    // Transform snake_case to camelCase
    return this.transformEvaluationMetrics(rawMetrics);
  }

  /**
   * Get model performance metrics
   * FIXED: Transforms response for UI compatibility
   */
  async getModelPerformanceMetrics(): Promise<ModelMetrics> {
    const response = await api.get('/admin/ml/metrics/model-performance');
    
    // Extract metrics from response
    const rawMetrics = response.metrics || response;
    
    // Transform to frontend format
    return this.transformEvaluationMetrics(rawMetrics);
  }

  // ============================================================================
  // DEMO FUNCTIONALITY
  // ============================================================================
  
  /**
   * FIXED: Now returns metadata about the demo system instead of hardcoded user IDs
   */
  async getDemoUserIds(): Promise<DemoUserIds> {
    return api.get<DemoUserIds>('/admin/demo/user-ids');
  }

  /**
   * DEMAND 3: Get live demo prediction comparison
   * FIXED: Now accepts ANY user ID - no client-side validation
   */
  async getDemoUserPrediction(userId: string): Promise<DemoUserPrediction> {
    return api.get<DemoUserPrediction>(`/admin/demo/user-prediction/${userId}`);
  }

  /**
   * DEMAND 1: Seed a new demo user into the database
   * FIXED: Now accepts ANY Instacart user ID - no client-side validation
   */
  async seedDemoUser(instacartUserId: string): Promise<any> {
    return api.post(`/admin/demo/seed-user/${instacartUserId}`);
  }

  // ============================================================================
  // ML SERVICE MANAGEMENT
  // ============================================================================
  
  /**
   * Get ML service status and health
   */
  async getMLServiceStatus(): Promise<any> {
    return api.get('/admin/ml-service/status');
  }

  /**
   * Get architecture status
   */
  async getArchitectureStatus(): Promise<any> {
    return api.get('/admin/architecture/status');
  }

  // ============================================================================
  // READ-ONLY DATA VIEWS (Matching backend routes)
  // ============================================================================
  
  /**
   * Get all products (read-only - seeded via database only)
   */
  async getProducts(params?: {
    page?: number;
    limit?: number;
    search?: string;
    category?: string;
    isActive?: boolean;
    sort?: string;
    order?: 'asc' | 'desc';
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.isActive !== undefined) queryParams.append('isActive', params.isActive.toString());
    if (params?.sort) queryParams.append('sort', params.sort);
    if (params?.order) queryParams.append('order', params.order);

    return api.get(`/admin/products?${queryParams.toString()}`);
  }

  /**
   * Get all users (read-only)
   */
  async getUsers(params?: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
    isActive?: boolean;
    sort?: string;
    order?: 'asc' | 'desc';
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.role) queryParams.append('role', params.role);
    if (params?.isActive !== undefined) queryParams.append('isActive', params.isActive.toString());
    if (params?.sort) queryParams.append('sort', params.sort);
    if (params?.order) queryParams.append('order', params.order);

    return api.get(`/admin/users?${queryParams.toString()}`);
  }

  /**
   * Get all orders (read-only)
   */
  async getOrders(params?: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    startDate?: string;
    endDate?: string;
    sort?: string;
    order?: 'asc' | 'desc';  
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.startDate) queryParams.append('startDate', params.startDate);
    if (params?.endDate) queryParams.append('endDate', params.endDate);
    if (params?.sort) queryParams.append('sort', params.sort);
    if (params?.order) queryParams.append('order', params.order);

    return api.get(`/admin/orders?${queryParams.toString()}`);
  }
}

export const adminService = new AdminService();
export default adminService;

// ============================================================================
// ARCHITECTURE FIX COMPLETE:
// 
// ✅ FIXED DATA TRANSFORMATION:
// - Added transformEvaluationMetrics method to convert snake_case to camelCase
// - Handles various response structures from the ML service
// - Provides fallback values for missing fields
// 
// ✅ UPDATED METHODS:
// - triggerModelEvaluation now transforms the response
// - getModelPerformanceMetrics now transforms the response
// - Both methods return properly formatted ModelMetrics
// 
// ✅ BENEFITS:
// - UI components receive consistent camelCase data
// - No breaking changes to existing components
// - Graceful handling of different ML service response formats
// 
// The frontend can now properly display model evaluation results
// regardless of the ML service's snake_case response format.
// ============================================================================