import { api } from '@/services/api.client';

export interface Product {
  productId: number;
  product_name: string;
  aisle_id: number;
  department_id: number;
  aisle_name: string;
  department_name: string;
  description: string | null;
  price: number | null;
  image_url: string | null;
}

export interface Department {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  parentId?: string;
  isActive: boolean;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ProductFilters {
  offset?: number;
  limit?: number;
  sort?: string;
  search?: string;
  categories?: string[];
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  onSale?: boolean;
}

class ProductService {
  
  // ============================================================================
  // CORE PRODUCT BROWSING (Read-only operations)
  // ============================================================================

  // Get all products with filters
  async getProducts(filters: ProductFilters = {}): Promise<ProductsResponse> {
    const params = new URLSearchParams();
    
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.sort) params.append('sort', filters.sort);
    if (filters.search) params.append('search', filters.search);
    if (filters.categories?.length) {
      filters.categories.forEach(cat => params.append('categories', cat));
    }
    if (filters.minPrice !== undefined) params.append('minPrice', filters.minPrice.toString());
    if (filters.maxPrice !== undefined) params.append('maxPrice', filters.maxPrice.toString());
    if (filters.inStock) params.append('inStock', 'true');
    if (filters.onSale) params.append('onSale', 'true');

    return api.get<ProductsResponse>(`/products?${params.toString()}`);
  }

  // Get single product
  async getProduct(id: number): Promise<Product> {
    return api.get<Product>(`/products/${id}`);
  }

  // Get product by department
  async getProductsByDepartment(departmentId: number): Promise<Product> {
    return api.get<Product>(`/products/department/${departmentId}`);
  }

  // Get product by aisle number
  async getProductsByAisle(aisleId: number): Promise<Product> {
    return api.get<Product>(`/products/aisle/${aisleId}`);
  }

  // Get products by category
  async getProductsByCategory(categoryId: string, filters: ProductFilters = {}): Promise<ProductsResponse> {
    return this.getProducts({ ...filters, categories: [categoryId] });
  }

  // Search products
  async searchProducts(query: string, filters: ProductFilters = {}): Promise<ProductsResponse> {
    return this.getProducts({ ...filters, search: query });
  }

  // Get product recommendations
  async getRecommendations(productId: number, limit: number = 4): Promise<Product[]> {
    return api.get<Product[]>(`/products/${productId}/recommendations?limit=${limit}`);
  }

  // ============================================================================
  // CATEGORY OPERATIONS (Read-only)
  // ============================================================================

  // Get departments
  async getDepartments(): Promise<Department[]> {
    const response = await api.get('/departments');
    return response.data.departments || [];
  }

  // Get category by ID
  async getDepartment(id: string): Promise<Department> {
    return api.get<Department>(`/products/department/${id}`);
  }

  // ============================================================================
  // USER INTERACTION TRACKING
  // ============================================================================

  // TODO: Track product view - use in admin?
  async trackProductView(productId: number): Promise<void> {
    return api.post(`/products/${productId}/view`);
  }

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================

  // Get price range for filters
  async getPriceRange(): Promise<{ min: number; max: number }> {
    return api.get<{ min: number; max: number }>('/products/price-range');
  }

  // Format price for display
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  }
}

export const productService = new ProductService();
