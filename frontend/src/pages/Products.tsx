import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, Grid, List } from 'lucide-react';
import { useQuery } from 'react-query';
import { productService } from '@/services/product.service';
import ProductCard from '@/components/products/ProductCard';
import ProductListItem from '@/components/products/ProductListItem';
import CategoryFilter from '@/components/products/CategoryFilter';
import PriceRangeFilter from '@/components/products/PriceRangeFilter';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import Pagination from '@/components/common/Pagination';
import SortDropdown, {SortOption} from "@/components/products/SortDropdown.tsx";

interface FilterState {
  categories: string[];
  priceRange: [number, number];
  inStock: boolean;
  onSale: boolean;
}

const Products: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOption, setSortOption] = useState<SortOption>('popularity');
  
  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    priceRange: [0, 100],
    inStock: false,
    onSale: false
  });

  const itemsPerPage = 25;

  // Fetch products with corrected sort parameters
  const { data, isLoading, error } = useQuery(
    ['products', currentPage, sortOption, filters, searchQuery],
    () => productService.getProducts({
      offset: itemsPerPage * (currentPage - 1),
      limit: itemsPerPage,
      sort: sortOption,
      search: searchQuery,
      categories: filters.categories,
      minPrice: filters.priceRange[0],
      maxPrice: filters.priceRange[1],
      inStock: filters.inStock,
      onSale: filters.onSale
    }),
    { 
      keepPreviousData: true,
      staleTime: 5 * 60 * 1000,
    }
  );

  // Fetch categories for filter
  const { data: categories } = useQuery(
    'categories',
    () => productService.getCategories(),
    { staleTime: 10 * 60 * 1000 }
  );

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    setSearchParams(searchQuery ? { q: searchQuery } : {});
  };

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1);
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      categories: [],
      priceRange: [0, 100],
      inStock: false,
      onSale: false
    });
    setCurrentPage(1);
  };

  // Update URL when search changes
  useEffect(() => {
    const currentSearch = searchParams.get('q') || '';
    if (currentSearch !== searchQuery) {
      setSearchQuery(currentSearch);
    }
  }, [searchParams]);

  const products = data?.products || [];
  const totalProducts = data?.total || 0;
  const totalPages = Math.ceil(totalProducts / itemsPerPage);

  // Calculate active filter count
  const activeFilterCount = 
    filters.categories.length + 
    (filters.inStock ? 1 : 0) + 
    (filters.onSale ? 1 : 0) +
    (filters.priceRange[0] > 0 || filters.priceRange[1] < 100 ? 1 : 0);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search products..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
              </div>
            </form>

            {/* Controls */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Filter size={20} />
                Filters
                {activeFilterCount > 0 && (
                  <span className="ml-1 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                    {activeFilterCount}
                  </span>
                )}
              </button>

              {/* FIXED: Updated to use new sort dropdown */}
              <SortDropdown value={sortOption} onChange={setSortOption} />

              <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded ${viewMode === 'grid' 
                    ? 'bg-white dark:bg-gray-600 shadow-sm' 
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                  } transition-all`}
                >
                  <Grid size={20} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded ${viewMode === 'list' 
                    ? 'bg-white dark:bg-gray-600 shadow-sm' 
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                  } transition-all`}
                >
                  <List size={20} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <AnimatePresence>
            {showFilters && (
              <motion.aside
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -300, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="w-64 flex-shrink-0"
              >
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Filters
                    </h3>
                    {activeFilterCount > 0 && (
                      <button
                        onClick={clearFilters}
                        className="text-sm text-indigo-600 hover:text-indigo-700"
                      >
                        Clear all
                      </button>
                    )}
                  </div>

                  <div className="space-y-6">
                    {/* Categories */}
                    <CategoryFilter
                      categories={categories || []}
                      selected={filters.categories}
                      onChange={(categories) => handleFilterChange({ categories })}
                    />

                    {/* Price Range */}
                    <PriceRangeFilter
                      value={filters.priceRange}
                      onChange={(priceRange) => handleFilterChange({ priceRange })}
                    />

                    {/* Stock & Sale Filters */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={filters.inStock}
                          onChange={(e) => handleFilterChange({ inStock: e.target.checked })}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          In Stock Only
                        </span>
                      </label>

                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={filters.onSale}
                          onChange={(e) => handleFilterChange({ onSale: e.target.checked })}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          On Sale
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <div className="flex-1">
            {/* Results Summary */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {searchQuery ? `Search results for "${searchQuery}"` : 'All Products'}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {totalProducts} products found
                </p>
              </div>
            </div>

            {/* Loading State */}
            {isLoading && (
              <div className="flex justify-center py-12">
                <LoadingSpinner />
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-12">
                <p className="text-red-600 dark:text-red-400">
                  Error loading products. Please try again.
                </p>
              </div>
            )}

            {/* Products Grid/List */}
            {!isLoading && !error && (
              <>
                {products.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-600 dark:text-gray-400">
                      No products found. Try adjusting your filters.
                    </p>
                  </div>
                ) : (
                  <>
                    {viewMode === 'grid' ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {products.map((product, index) => (
                          <motion.div
                            key={product.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                          >
                            <ProductCard product={product} />
                          </motion.div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {products.map((product, index) => (
                          <motion.div
                            key={product.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                          >
                            <ProductListItem product={product} />
                          </motion.div>
                        ))}
                      </div>
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="mt-12 flex justify-center">
                        <Pagination
                          currentPage={currentPage}
                          totalPages={totalPages}
                          onPageChange={setCurrentPage}
                        />
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Products;