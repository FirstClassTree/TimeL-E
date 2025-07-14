// frontend/src/pages/Orders.tsx
import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Package, Clock, CheckCircle, XCircle, Truck,
  Eye, RefreshCcw, Calendar, DollarSign
} from 'lucide-react';
import { orderService } from '@/services/order.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import EmptyState from '@/components/common/EmptyState';

interface Order {
  id: string;
  orderNumber: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  total: number;
  items: Array<{
    id: string;
    name: string;
    price: number;
    quantity: number;
    image: string;
  }>;
  createdAt: string;
  deliveryDate?: string;
  trackingNumber?: string;
}

const Orders: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'>('all');

  const { data: orders, isLoading, error, refetch } = useQuery<Order[]>(
    ['orders'],
    orderService.getOrders,
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const getStatusIcon = (status: Order['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="text-yellow-500" size={16} />;
      case 'processing':
        return <Package className="text-blue-500" size={16} />;
      case 'shipped':
        return <Truck className="text-indigo-500" size={16} />;
      case 'delivered':
        return <CheckCircle className="text-green-500" size={16} />;
      case 'cancelled':
        return <XCircle className="text-red-500" size={16} />;
      default:
        return <Clock className="text-gray-500" size={16} />;
    }
  };

  const getStatusColor = (status: Order['status']) => {
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

  const filteredOrders = orders?.filter(order => 
    filter === 'all' || order.status === filter
  ) || [];

  const statusCounts = orders?.reduce((acc, order) => {
    acc[order.status] = (acc[order.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  if (isLoading) return <LoadingSpinner fullScreen />;

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Failed to load orders
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Something went wrong while fetching your orders.
          </p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 mx-auto bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <RefreshCcw size={20} />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!orders || orders.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <EmptyState
          icon={Package}
          title="No orders yet"
          description="Start shopping to see your order history here."
          actionText="Browse Products"
          actionLink="/products"
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          My Orders
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track and manage your order history
        </p>
      </div>

      {/* Order Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
        <motion.button
          onClick={() => setFilter('all')}
          className={`p-4 rounded-lg border-2 transition-colors ${
            filter === 'all'
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          }`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {orders.length}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">All Orders</div>
        </motion.button>

        {['pending', 'processing', 'shipped', 'delivered', 'cancelled'].map((status) => (
          <motion.button
            key={status}
            onClick={() => setFilter(status as any)}
            className={`p-4 rounded-lg border-2 transition-colors ${
              filter === status
                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {statusCounts[status] || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 capitalize">
              {status}
            </div>
          </motion.button>
        ))}
      </div>

      {/* Orders List */}
      <div className="space-y-6">
        {filteredOrders.map((order) => (
          <motion.div
            key={order.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden"
          >
            {/* Order Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Order #{order.orderNumber}
                  </h3>
                  <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                    {getStatusIcon(order.status)}
                    <span className="capitalize">{order.status}</span>
                  </div>
                </div>
                <Link
                  to={`/orders/${order.id}`}
                  className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 transition-colors"
                >
                  <Eye size={16} />
                  View Details
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Calendar size={16} />
                  <span>Ordered: {new Date(order.createdAt).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <DollarSign size={16} />
                  <span>Total: ${order.total.toFixed(2)}</span>
                </div>
                {order.trackingNumber && (
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <Truck size={16} />
                    <span>Tracking: {order.trackingNumber}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Order Items */}
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {order.items.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                      <img
                        src={item.image}
                        alt={item.name}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white truncate">
                        {item.name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Qty: {item.quantity} × ${item.price.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
                {order.items.length > 3 && (
                  <div className="flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                    +{order.items.length - 3} more items
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {filteredOrders.length === 0 && filter !== 'all' && (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No {filter} orders
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            You don't have any orders with {filter} status.
          </p>
        </div>
      )}
    </div>
  );
};

export default Orders;