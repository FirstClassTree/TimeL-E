import React, { useState } from 'react';
import { Calendar } from 'lucide-react';

interface DateRangePickerProps {
  onDateChange: (startDate: Date, endDate: Date) => void;
  defaultRange?: { start: Date; end: Date };
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({ 
  onDateChange, 
  defaultRange 
}) => {
  const [startDate, setStartDate] = useState(
    defaultRange?.start || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  );
  const [endDate, setEndDate] = useState(defaultRange?.end || new Date());

  const handleStartDateChange = (date: string) => {
    const newStartDate = new Date(date);
    setStartDate(newStartDate);
    onDateChange(newStartDate, endDate);
  };

  const handleEndDateChange = (date: string) => {
    const newEndDate = new Date(date);
    setEndDate(newEndDate);
    onDateChange(startDate, newEndDate);
  };

  const formatDateForInput = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="flex items-center space-x-4 bg-white rounded-lg shadow p-4">
      <Calendar className="h-5 w-5 text-gray-400" />
      
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">From:</label>
        <input
          type="date"
          value={formatDateForInput(startDate)}
          onChange={(e) => handleStartDateChange(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">To:</label>
        <input
          type="date"
          value={formatDateForInput(endDate)}
          onChange={(e) => handleEndDateChange(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );
};

export default DateRangePicker;