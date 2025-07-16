import React, { useState } from 'react';
import { DollarSign } from 'lucide-react';

interface PriceRangeFilterProps {
  minPrice: number;
  maxPrice: number;
  onPriceChange: (min: number, max: number) => void;
}

const PriceRangeFilter: React.FC<PriceRangeFilterProps> = ({
  minPrice,
  maxPrice,
  onPriceChange
}) => {
  const [localMin, setLocalMin] = useState(minPrice);
  const [localMax, setLocalMax] = useState(maxPrice);

  const handleMinChange = (value: number) => {
    setLocalMin(value);
    onPriceChange(value, localMax);
  };

  const handleMaxChange = (value: number) => {
    setLocalMax(value);
    onPriceChange(localMin, value);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center mb-3">
        <DollarSign className="h-4 w-4 text-gray-500 mr-2" />
        <span className="font-medium text-gray-700">Price Range</span>
      </div>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Min Price</label>
          <input
            type="number"
            min="0"
            max={localMax}
            value={localMin}
            onChange={(e) => handleMinChange(Number(e.target.value))}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0"
          />
        </div>
        
        <div>
          <label className="block text-sm text-gray-600 mb-1">Max Price</label>
          <input
            type="number"
            min={localMin}
            value={localMax}
            onChange={(e) => handleMaxChange(Number(e.target.value))}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="999"
          />
        </div>
        
        <div className="text-sm text-gray-600">
          ${localMin} - ${localMax}
        </div>
      </div>
    </div>
  );
};

export default PriceRangeFilter;