// frontend/src/pages/admin/Dashboard.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from 'react-query';
import { 
  TrendingUp, Users, ShoppingCart, Brain, 
  Package, DollarSign, Activity, AlertCircle,
  Calendar, ArrowUp, ArrowDown, BarChart3
} from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { adminService } from '@/services/admin.service';
import { predictionService } from '@/services/prediction.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import MetricCard from '@/components/admin/MetricCard';
import DateRangePicker from '@/components/admin/DateRangePicker';

const AdminDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState({ start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), end: new Date() });

  // Fetch dashboard data
  const { data: dashboardData, isLoading: isDashboardLoading } = useQuery(
    ['admin-dashboard', dateRange],
    () => adminService.getDashboardStats(dateRange),
    { staleTime: 5 * 60 * 1000 }
  );

  const { data: modelMetrics, isLoading: isModelLoading } = useQuery(
    'model-metrics',
    predictionService.getModelMetrics,
    { staleTime: 10 * 60 * 1000 }  // Standardized: 10min
  );

  const { data: onlineMetrics } = useQuery(
    'online-metrics',
    predictionService.getOnlineMetrics,
    { staleTime: 2 * 60 * 1000 }   // Standardized: 2min
  );

  if (isDashboardLoading || isMLLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const stats = dashboardData?.stats || {
    totalRevenue: 0,
    totalOrders: 0,
    totalUsers: 0,
    activeUsers: 0,
    avgOrderValue: 0,
    conversionRate: 0,
    revenueGrowth: 0,
    orderGrowth: 0,
    userGrowth: 0
  };

  const chartData = dashboardData?.chartData || {
    salesOverTime: [],
    ordersByStatus: [],
    topProducts: [],
    userActivity: [],
    categoryDistribution: []
  };

  const COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#3B82F6'];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Admin Dashboard
          </h1>
          <div className="flex items-center justify-between">
            <p className="text-gray-600 dark:text-gray-300">
              Welcome back! Here's what's happening with your store.
            </p>
            <DateRangePicker value={dateRange} onChange={setDateRange} />
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Revenue"
            value={`$${stats.totalRevenue.toLocaleString()}`}
            change={stats.revenueGrowth}
            icon={DollarSign}
            color="indigo"
          />
          <MetricCard
            title="Total Orders"
            value={stats.totalOrders.toLocaleString()}
            change={stats.orderGrowth}
            icon={ShoppingCart}
            color="purple"
          />
          <MetricCard
            title="Active Users"
            value={stats.activeUsers.toLocaleString()}
            subtitle={`of ${stats.totalUsers.toLocaleString()} total`}
            change={stats.userGrowth}
            icon={Users}
            color="pink"
          />
          <MetricCard
            title="Avg Order Value"
            value={`$${stats.avgOrderValue.toFixed(2)}`}
            change={stats.conversionRate}
            icon={TrendingUp}
            color="green"
          />
        </div>

        {/* ML Performance Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-500" />
              ML Model Performance
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {modelMetrics?.lastUpdated ? new Date(modelMetrics.lastUpdated).toLocaleString() : 'N/A'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600">
                {((modelMetrics?.precisionAt10 || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Precision@10</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {((modelMetrics?.recallAt10 || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Recall@10</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-pink-600">
                {((modelMetrics?.hitRate || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {((modelMetrics?.ndcg || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">NDCG</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {((modelMetrics?.f1Score || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">F1 Score</div>
            </div>
          </div>

          {onlineMetrics && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Online Metrics
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {((onlineMetrics.autoCartAcceptanceRate || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Cart Acceptance Rate</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-teal-600">
                    {onlineMetrics.avgEditDistance?.toFixed(1) || '0'}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Avg Edit Distance</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {((onlineMetrics.cartValueUplift || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Cart Value Uplift</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {onlineMetrics.userSatisfactionScore?.toFixed(1) || '0'}/5
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">User Satisfaction</div>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sales Over Time */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Sales Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData.salesOverTime}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                <XAxis dataKey="date" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '0.5rem' 
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#6366F1" 
                  fillOpacity={1} 
                  fill="url(#colorRevenue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Order Status Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Order Status Distribution
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.ordersByStatus}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.ordersByStatus.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Top Products */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Top Products
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.topProducts.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                <XAxis type="number" stroke="#9CA3AF" />
                <YAxis dataKey="name" type="category" stroke="#9CA3AF" width={100} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '0.5rem' 
                  }} 
                />
                <Bar dataKey="sales" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* User Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              User Activity Heatmap
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData.userActivity}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                <XAxis dataKey="hour" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '0.5rem' 
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="active" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  dot={{ fill: '#10B981', r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="orders" 
                  stroke="#F59E0B" 
                  strokeWidth={2}
                  dot={{ fill: '#F59E0B', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Activity
          </h3>
          <div className="space-y-4">
            {dashboardData?.recentActivity?.map((activity: any, index: number) => (
              <div key={index} className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    activity.type === 'order' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' :
                    activity.type === 'user' ? 'bg-green-100 dark:bg-green-900/30 text-green-600' :
                    'bg-purple-100 dark:bg-purple-900/30 text-purple-600'
                  }`}>
                    {activity.type === 'order' ? <ShoppingCart size={20} /> :
                     activity.type === 'user' ? <Users size={20} /> :
                     <Brain size={20} />}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{activity.description}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{activity.timestamp}</p>
                  </div>
                </div>
                {activity.value && (
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {activity.value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AdminDashboard;