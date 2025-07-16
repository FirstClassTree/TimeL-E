// frontend/src/components/search/SearchModal.tsx
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Clock, TrendingUp, Package, ArrowRight } from 'lucide-react';
import { useQuery } from 'react-query';
import { productService } from '@/services/product.service';
import { Link } from 'react-router-dom';

interface SearchModalProps {
  onClose: () => void;
}

interface SearchResult {
  id: string;
  name: string;
  price: number;
  image: string;
  category: string;
}

interface SearchSuggestion {
  id: string;
  text: string;
  type: 'recent' | 'popular' | 'category';
}

const SearchModal: React.FC<SearchModalProps> = ({ onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([
    'organic bananas',
    'whole wheat bread',
    'greek yogurt'
  ]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Mock popular searches and categories
  const popularSearches = [
    'organic vegetables',
    'dairy products',
    'fresh fruits',
    'gluten-free',
    'protein bars'
  ];

  const categories = [
    'Produce',
    'Dairy & Eggs',
    'Meat & Seafood',
    'Bakery',
    'Pantry',
    'Frozen Foods'
  ];

  // Search products
  const { data: searchResults, isLoading } = useQuery<SearchResult[]>(
    ['search', searchTerm],
    () => productService.searchProducts(searchTerm),
    {
      enabled: searchTerm.length > 2,
      staleTime: 30000, // 30 seconds
    }
  );

  useEffect(() => {
    // Focus input on mount
    if (inputRef.current) {
      inputRef.current.focus();
    }

    // Handle escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleSearch = (term: string) => {
    if (term.trim()) {
      // Add to recent searches
      setRecentSearches(prev => {
        const filtered = prev.filter(item => item !== term);
        return [term, ...filtered].slice(0, 5);
      });
      
      // Navigate to search results
      onClose();
      window.location.href = `/products?search=${encodeURIComponent(term)}`;
    }
  };

  const handleQuickSearch = (term: string) => {
    setSearchTerm(term);
    handleSearch(term);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-start justify-center pt-20"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className="w-full max-w-2xl mx-4 bg-white dark:bg-gray-800 rounded-lg shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              ref={inputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch(searchTerm);
                }
              }}
              placeholder="Search for products..."
              className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-lg"
            />
            <button
              onClick={onClose}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Search Results or Suggestions */}
        <div className="max-h-96 overflow-y-auto">
          {searchTerm.length > 2 ? (
            // Search Results
            <div className="p-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
              ) : searchResults && searchResults.length > 0 ? (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                    Search Results ({searchResults.length})
                  </h3>
                  {searchResults.slice(0, 6).map((product) => (
                    <Link
                      key={product.id}
                      to={`/products/${product.id}`}
                      onClick={onClose}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                        <img
                          src={product.image}
                          alt={product.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {product.name}
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {product.category} • ${product.price.toFixed(2)}
                        </p>
                      </div>
                      <ArrowRight size={16} className="text-gray-400" />
                    </Link>
                  ))}
                  
                  {searchResults.length > 6 && (
                    <button
                      onClick={() => handleSearch(searchTerm)}
                      className="w-full p-3 text-center text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
                    >
                      View all {searchResults.length} results
                    </button>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    No products found for "{searchTerm}"
                  </p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                    Try different keywords or browse categories
                  </p>
                </div>
              )}
            </div>
          ) : (
            // Search Suggestions
            <div className="p-4 space-y-6">
              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
                      <Clock size={16} />
                      Recent Searches
                    </h3>
                    <button
                      onClick={clearRecentSearches}
                      className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="space-y-1">
                    {recentSearches.map((search, index) => (
                      <button
                        key={index}
                        onClick={() => handleQuickSearch(search)}
                        className="flex items-center gap-3 w-full p-2 text-left rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <Search size={16} className="text-gray-400" />
                        <span className="text-gray-700 dark:text-gray-300">{search}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Popular Searches */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                  <TrendingUp size={16} />
                  Popular Searches
                </h3>
                <div className="flex flex-wrap gap-2">
                  {popularSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickSearch(search)}
                      className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              </div>

              {/* Categories */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                  <Package size={16} />
                  Browse Categories
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {categories.map((category, index) => (
                    <Link
                      key={index}
                      to={`/products?category=${encodeURIComponent(category)}`}
                      onClick={onClose}
                      className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-center"
                    >
                      <span className="text-gray-700 dark:text-gray-300 text-sm font-medium">
                        {category}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Press <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">Escape</kbd> to close
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SearchModal;