import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, Grid, List } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
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
}

const Products: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [searchInput, setSearchInput] = useState(searchParams.get('q') || '');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOption, setSortOption] = useState<SortOption>('popularity');

  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    priceRange: [0, 300]
  });

  const itemsPerPage = 25;

  // Fetch price range for filter initialization
  const { data: priceRangeData } = useQuery(
    'price-range',
    () => productService.getPriceRange(),
    {
      staleTime: 10 * 60 * 1000,
      onSuccess: (data) => {
        // Initialize price range filter with actual min/max values
        setFilters(prev => ({
          ...prev,
          priceRange: [data.min, data.max]
        }));
      }
    }
  );

  // Fetch departments for filter
  const { data: departments, isLoading: departmentsLoading } = useQuery(
    'departments',
    () => productService.getDepartments(),
    { staleTime: 10 * 60 * 1000 }
  );

  // Fetch products with all dependencies properly tracked
  const { data, isLoading, error, refetch } = useQuery(
    ['products', currentPage, sortOption, filters.categories, filters.priceRange, searchQuery],
    () => productService.getProducts({
      offset: itemsPerPage * (currentPage - 1),
      limit: itemsPerPage,
      sort: sortOption,
      search: searchQuery || undefined, // Don't send empty string
      categories: filters.categories.length > 0 ? filters.categories : undefined,
      minPrice: filters.priceRange[0],
      maxPrice: filters.priceRange[1]
    }),
    {
      keepPreviousData: true,
      staleTime: 1 * 60 * 1000,
      enabled: true,
    }
  );

  // Handle search form submission
  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const trimmedQuery = searchInput.trim();
    setSearchQuery(trimmedQuery);
    setCurrentPage(1);

    // Update URL params
    if (trimmedQuery) {
      setSearchParams({ q: trimmedQuery });
    } else {
      setSearchParams({});
    }
  }, [searchInput, setSearchParams]);

  // Handle filter changes with debouncing for better UX
  const handleFilterChange = useCallback((newFilters: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    const defaultPriceRange: [number, number] = priceRangeData
      ? [priceRangeData.min, priceRangeData.max]
      : [0, 300];

    setFilters({
      categories: [],
      priceRange: defaultPriceRange
    });
    setCurrentPage(1);
  }, [priceRangeData]);

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Handle sort change
  const handleSortChange = useCallback((newSort: SortOption) => {
    setSortOption(newSort);
    setCurrentPage(1); // Reset to first page when sort changes
  }, []);

  // Update search input when URL changes
  useEffect(() => {
    const urlSearch = searchParams.get('q') || '';
    if (urlSearch !== searchInput) {
      setSearchInput(urlSearch);
      setSearchQuery(urlSearch);
    }
  }, [searchParams]);

  // Initialize filters when price range data is loaded
  useEffect(() => {
    if (priceRangeData && filters.priceRange[0] === 0 && filters.priceRange[1] === 300) {
      setFilters(prev => ({
        ...prev,
        priceRange: [priceRangeData.min, priceRangeData.max]
      }));
    }
  }, [priceRangeData, filters.priceRange]);

  const products = data?.products || [];

  // Calculate active filter count
  const activeFilterCount =
    filters.categories.length +
    (priceRangeData && (filters.priceRange[0] > priceRangeData.min || filters.priceRange[1] < priceRangeData.max) ? 1 : 0);

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
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search products..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition-colors"
                >
                  Search
                </button>
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

              <SortDropdown value={sortOption} onChange={handleSortChange} />

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
                        className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
                      >
                        Clear all
                      </button>
                    )}
                  </div>

                  <div className="space-y-6">
                    {/* Department Filter */}
                    {departmentsLoading ? (
                      <div className="animate-pulse">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                        <div className="space-y-2">
                          {[1, 2, 3].map(i => (
                            <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <CategoryFilter
                        categories={departments || []}
                        selected={filters.categories}
                        onChange={(categories) => handleFilterChange({ categories })}
                        title="Departments"
                      />
                    )}

                    {/* Price Range Filter */}
                    {priceRangeData && (
                      <PriceRangeFilter
                        value={filters.priceRange}
                        onChange={(priceRange) => handleFilterChange({ priceRange })}
                        min={priceRangeData.min}
                        max={priceRangeData.max}
                      />
                    )}
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
                  {isLoading ? 'Loading...' : `${data?.total?.toLocaleString()} products found`}
                  {currentPage > 1 && ` • Page ${currentPage}`}
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
                <p className="text-red-600 dark:text-red-400 mb-4">
                  Error loading products. Please try again.
                </p>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Products Grid/List */}
            {!isLoading && !error && (
              <>
                {products.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      No products found matching your criteria.
                    </p>
                    <button
                      onClick={clearFilters}
                      className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
                    >
                      Clear filters to see all products
                    </button>
                  </div>
                ) : (
                  <>
                    {viewMode === 'grid' ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {products.map((product, index) => (
                          <motion.div
                            key={product.productId}
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
                            key={product.productId}
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
                    {data?.has_next == true && (
                      <div className="mt-12 flex justify-center">
                        <Pagination
                          currentPage={currentPage}
                          totalPages={5}
                          onPageChange={handlePageChange}
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