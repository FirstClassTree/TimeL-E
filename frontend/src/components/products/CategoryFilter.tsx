import React from 'react';
import { Check } from 'lucide-react';

interface Category {
  id: string;
  name: string;
  isActive?: boolean;
}

interface CategoryFilterProps {
  categories: Category[];
  selected: string[];
  onChange: (categoryIds: string[]) => void;
}

const CategoryFilter: React.FC<CategoryFilterProps> = ({
  categories,
  selected,
  onChange
}) => {
  const handleCategoryToggle = (categoryId: string) => {
    const newSelected = selected.includes(categoryId)
      ? selected.filter(id => id !== categoryId)
      : [...selected, categoryId];
    onChange(newSelected);
  };

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-gray-900 dark:text-white">Departments</h4>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {categories.map((category) => (
          <label
            key={category.id}
            className="flex items-center space-x-3 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded-md transition-colors"
          >
            <div className="relative">
              <input
                type="checkbox"
                checked={selected.includes(category.id)}
                onChange={() => handleCategoryToggle(category.id)}
                className="sr-only"
              />
              <div className={`w-4 h-4 border-2 rounded flex items-center justify-center transition-colors ${
                selected.includes(category.id)
                  ? 'bg-indigo-600 border-indigo-600 text-white'
                  : 'border-gray-300 dark:border-gray-600'
              }`}>
                {selected.includes(category.id) && (
                  <Check size={12} className="text-white" />
                )}
              </div>
            </div>
            <span className="text-gray-700 dark:text-gray-300 flex-1">
              {category.name}
            </span>
          </label>
        ))}
      </div>
      {selected.length > 0 && (
        <button
          onClick={() => onChange([])}
          className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
        >
          Clear selection
        </button>
      )}
    </div>
  );
};

export default CategoryFilter;
