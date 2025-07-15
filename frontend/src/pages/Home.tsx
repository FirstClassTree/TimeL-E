// frontend/src/pages/Home.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingCart, Clock, Brain, TrendingUp, ChevronRight, Sparkles } from 'lucide-react';
import Hero from '@/components/home/Hero';
import FeatureCard from '@/components/home/FeatureCard';
import { useAuthStore } from '@/stores/auth.store';

const Home: React.FC = () => {
  const { user } = useAuthStore();

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Predictions',
      description: 'Our ML algorithm learns your shopping habits and predicts your weekly needs with remarkable accuracy.',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: Clock,
      title: 'Save Time Every Week',
      description: 'Automated weekly carts mean no more repetitive shopping lists. Spend time on what matters.',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: ShoppingCart,
      title: 'Smart Shopping',
      description: 'Review and customize your predicted basket before checkout. Full control, zero hassle.',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: TrendingUp,
      title: 'Adaptive Learning',
      description: 'The more you shop, the smarter it gets. Our system continuously improves its predictions.',
      color: 'from-orange-500 to-red-500'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Hero Section */}
      <Hero />

      {/* Features Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4 cursor-pointer">
              Improve your shopping experience with TimeL-E
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto cursor-pointer">
              Experience the future of grocery shopping with our advanced AI technology
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <FeatureCard key={index} {...feature} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section for logged-in users */}
      {user && (
        <section className="py-16 px-4 bg-gradient-to-r from-indigo-600 to-purple-600">
          <div className="max-w-4xl mx-auto text-center text-white">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <Sparkles className="w-16 h-16 mx-auto mb-6" />
              <h2 className="text-3xl font-bold mb-4">
                Your AI Basket is Ready!
              </h2>
              <p className="text-xl mb-8 opacity-90">
                We've analyzed your shopping patterns and prepared your weekly essentials
              </p>
              <Link
                to="/predicted-basket"
                className="inline-flex items-center px-8 py-4 bg-white text-indigo-600 font-bold rounded-full hover:bg-gray-100 transition-all transform hover:scale-105"
              >
                View My Predicted Basket
                <ChevronRight className="ml-2" />
              </Link>
            </motion.div>
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex justify-between items-center mb-12"
          >
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                Featured Products
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Handpicked selections just for you
              </p>
            </div>
            <Link
              to="/products"
              className="flex items-center text-indigo-600 hover:text-indigo-700 font-semibold"
            >
              View All Products
              <ChevronRight className="ml-1" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            {[
              { value: '50K+', label: 'Happy Customers' },
              { value: '95%', label: 'Prediction Accuracy' },
              { value: '2hrs', label: 'Average Time Saved' },
              { value: '4.9', label: 'Customer Rating' }
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.5 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <div className="text-4xl font-bold text-indigo-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-600 dark:text-gray-300">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section for non-logged users */}
      {!user && (
        <section className="py-20 px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-4xl mx-auto text-center"
          >
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
              Ready to Save Time on Grocery Shopping?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
              Join thousands of satisfied customers who've revolutionized their weekly shopping
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register"
                className="px-8 py-4 bg-indigo-600 text-white font-bold rounded-full hover:bg-indigo-700 transition-all transform hover:scale-105"
              >
                Get Started Free
              </Link>
              <Link
                to="/products"
                className="px-8 py-4 bg-gray-200 text-gray-800 font-bold rounded-full hover:bg-gray-300 transition-all transform hover:scale-105"
              >
                Browse Products
              </Link>
            </div>
          </motion.div>
        </section>
      )}
    </div>
  );
};

export default Home;