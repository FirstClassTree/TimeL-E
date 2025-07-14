import React from 'react';
import { Info } from 'lucide-react';

interface MetricExplanationProps {
  metric: string;
  description: string;
  calculation?: string;
  goodRange?: string;
}

const MetricExplanation: React.FC<MetricExplanationProps> = ({
  metric,
  description,
  calculation,
  goodRange
}) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-start">
        <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
        <div>
          <h4 className="font-semibold text-blue-900 mb-2">{metric}</h4>
          <p className="text-blue-800 text-sm mb-2">{description}</p>
          
          {calculation && (
            <div className="mb-2">
              <span className="font-medium text-blue-900 text-sm">Calculation: </span>
              <span className="text-blue-800 text-sm">{calculation}</span>
            </div>
          )}
          
          {goodRange && (
            <div>
              <span className="font-medium text-blue-900 text-sm">Good Range: </span>
              <span className="text-blue-800 text-sm">{goodRange}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricExplanation;