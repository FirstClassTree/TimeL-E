import { api } from '@/services/api.client';

export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string;
  price: number;
  compareAtPrice?: number;
  unit?: string;
  unitValue?: number;
  brand?: string;
  tags: string[];
  imageUrl?: string;
  additionalImages: string[];
  categoryId: string;
  category?: Category;
  stock: number;
  trackInventory: boolean;
  isActive: boolean;
  isFeatured: boolean;
  isOnSale: boolean;
  salePercentage: number;
  salePrice: number;
  inStock: boolean;
  nutritionalInfo: Record<string, any>;
  metadata: Record<string, any>;
  viewCount: number;
  purchaseCount: number;
  avgRating: number;
  reviewCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  parentId?: string;
  isActive: boolean;
  productCount?: number;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  offset: number;
  hasMore: boolean;
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
  featured?: boolean;
}

class ProductService {
  
  // ============================================================================
  // CORE PRODUCT BROWSING (Read-only operations)
  // ============================================================================

    async getProducts(filters: ProductFilters = {}): Promise<ProductsResponse> {
    const params = new URLSearchParams();
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
        return api.get<ProductsResponse>(`/products?${params.toString()}`);
  }
  /*
  // Get all products with filters
  async getProducts(filters: ProductFilters = {}): Promise<ProductsResponse> {
    const params = new URLSearchParams();
    
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.sort) params.append('sort', filters.sort);
    if (filters.search) params.append('search', filters.search);
    if (filters.categories?.length) {
      filters.categories.forEach(cat => params.append('categories[]', cat));
    }
    if (filters.minPrice !== undefined) params.append('minPrice', filters.minPrice.toString());
    if (filters.maxPrice !== undefined) params.append('maxPrice', filters.maxPrice.toString());
    if (filters.inStock) params.append('inStock', 'true');
    if (filters.onSale) params.append('onSale', 'true');
    //if (filters.featured) params.append('featured', 'true');

    return api.get<ProductsResponse>(`/products?${params.toString()}`);
  }
*/

  // Get single product
  async getProduct(id: bigint): Promise<Product> {
    return api.get<Product>(`/products/${id}`);
  }

  // Get product by department
  async getProductsByDepartment(departmentId: bigint): Promise<Product> {
    return api.get<Product>(`/products/department/${departmentId}`);
  }

  // Get product by aisle number
  async getProductsByAisle(aisleId: bigint): Promise<Product> {
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
  async getRecommendations(productId: string, limit: number = 4): Promise<Product[]> {
    return api.get<Product[]>(`/products/${productId}/recommendations?limit=${limit}`);
  }

  // ============================================================================
  // CATEGORY OPERATIONS (Read-only)
  // ============================================================================

  // Get categories
  async getCategories(): Promise<Category[]> {
    return api.get<Category[]>('/products/categories');
  }

  // Get category by ID
  async getCategory(id: string): Promise<Category> {
    return api.get<Category>(`/products/categories/${id}`);
  }

  // ============================================================================
  // USER INTERACTION TRACKING
  // ============================================================================

  // TODO: Track product view - use in admin?
  async trackProductView(productId: string): Promise<void> {
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

  //  TODO: Calculate discount percentage - use and show!
  calculateDiscount(price: number, compareAtPrice?: number): number {
    if (!compareAtPrice || compareAtPrice <= price) return 0;
    return Math.round(((compareAtPrice - price) / compareAtPrice) * 100);
  }
}

export const productService = new ProductService();