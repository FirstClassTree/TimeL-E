import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Package, Truck, CheckCircle, Clock, 
  MapPin, Calendar, DollarSign, Phone,
  Download, RefreshCcw, Star
} from 'lucide-react';
import { orderService} from '@/services/order.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import toast from 'react-hot-toast';

interface OrderDetail {
  orderId: number;
  orderNumber: number;
  status: 'PENDING' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  total: number;
  items: Array<{
    id: string;
    name: string;
    price: number;
    quantity: number;
    image: string;
    category: string;
  }>;
  createdAt: string;
  estimatedDelivery?: string;
}

const OrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: order, isLoading, error } = useQuery<OrderDetail>(
    ['order', id],
    () => orderService.getOrder(id!),
    {
      enabled: !!id,
    }
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="text-yellow-500" size={20} />;
      case 'processing':
        return <Package className="text-blue-500" size={20} />;
      case 'shipped':
        return <Truck className="text-indigo-500" size={20} />;
      case 'delivered':
        return <CheckCircle className="text-green-500" size={20} />;
      default:
        return <Clock className="text-gray-500" size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'shipped':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
      case 'delivered':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const handleReorder = () => {
    if (!order) return;
    
    // Add all items to cart and navigate to cart
    // This would be implemented with your cart store
    toast.success('Items added to cart');
    navigate('/cart');
  };

  if (isLoading) return <LoadingSpinner fullScreen />;

  if (error || !order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Order not found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The order you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/orders')}
            className="flex items-center gap-2 mx-auto bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/orders')}
          className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 transition-colors mb-4"
        >
          <ArrowLeft size={16} />
          Back to Orders
        </button>
        
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Order #{order.orderNumber}
            </h1>
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                {getStatusIcon(order.status)}
                <span className="capitalize">{order.status}</span>
              </div>
              <span className="text-gray-500 dark:text-gray-400">
                Placed on {new Date(order.createdAt).toLocaleDateString()}
              </span>
            </div>
          </div>
          
          <div className="flex gap-2">
            
            <button
              onClick={handleReorder}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCcw size={16} />
              Reorder
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Items */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Order Items ({order.items.length})
              </h3>
            </div>
            
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {order.items.map((item) => (
                <div key={item.id} className="p-6 flex items-center gap-4">
                  <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                    <img
                      src={item.image}
                      alt={item.name}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                      {item.name}
                    </h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {item.category}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Quantity: {item.quantity}
                    </p>
                  </div>
                  
                  <div className="text-right">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      ${(item.price * item.quantity).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      ${item.price.toFixed(2)} each
                    </p>
                  </div>
                </div>
              ))}
            </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Order Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Order Summary
            </h3>
            
            <div className="space-y-1">
              <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div className="flex justify-between">
                  <span className="font-semibold text-gray-900 dark:text-white">Total</span>
                  <span className="font-semibold text-gray-900 dark:text-white">${order.total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Delivery Information */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Delivery Information
            </h3>
            
            <div className="space-y-3">
              {order.estimatedDelivery && (
                <div className="flex items-center gap-3">
                  <Calendar className="text-gray-400" size={16} />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Estimated Delivery
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(order.estimatedDelivery).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
              
              {order.orderNumber && (
                <div className="flex items-center gap-3">
                  <Package className="text-gray-400" size={16} />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Order Number
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {order.orderNumber}
                    </p>
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* Actions */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Need Help?
            </h3>
            
            <div className="space-y-3">
              <button className="flex items-center gap-3 w-full p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <Phone className="text-gray-400" size={16} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Contact Support
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Request help with your order
                  </p>
                </div>
              </button>
              
              <button className="flex items-center gap-3 w-full p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <Download className="text-gray-400" size={16} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Download Invoice
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    PDF receipt
                  </p>
                </div>
              </button>

              {order.status === 'delivered' && (
                <button className="flex items-center gap-3 w-full p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <Star className="text-gray-400" size={16} />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Rate & Review
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Share your shopping experience
                    </p>
                  </div>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
};

export default OrderDetail;