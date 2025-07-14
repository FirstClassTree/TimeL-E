import React, { useState, useEffect } from 'react';
import { Search, ShoppingCart, User, Calendar, CreditCard, MapPin, Phone, Mail, Eye, EyeOff, Plus, Minus, Trash2, Star } from 'lucide-react';
import {sendAddItemToCartRequest} from "./userService";

// Mock data for demonstration
const mockItems = [
  {
    id: 1,
    name: "Fresh Organic Apples",
    description: "Crisp and sweet organic apples, perfect for snacking or baking",
    tags: ["fruit", "organic", "healthy", "fresh"],
    imageUrl: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=200&h=200&fit=crop"
  },
  {
    id: 2,
    name: "Whole Grain Bread",
    description: "Nutritious whole grain bread, freshly baked daily",
    tags: ["bread", "whole grain", "bakery", "healthy"],
    imageUrl: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=200&h=200&fit=crop"
  },
  {
    id: 3,
    name: "Premium Olive Oil",
    description: "Extra virgin olive oil from Mediterranean olives",
    tags: ["oil", "cooking", "mediterranean", "premium"],
    imageUrl: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200&h=200&fit=crop"
  },
  {
    id: 4,
    name: "Fresh Salmon Fillet",
    description: "Wild-caught salmon fillet, rich in omega-3",
    tags: ["fish", "seafood", "protein", "healthy"],
    imageUrl: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=200&h=200&fit=crop"
  },
  {
    id: 5,
    name: "Greek Yogurt",
    description: "Creamy Greek yogurt with probiotics",
    tags: ["dairy", "yogurt", "protein", "healthy"],
    imageUrl: "https://images.unsplash.com/photo-1571212515416-0b21e29c634d?w=200&h=200&fit=crop"
  },
  {
    id: 6,
    name: "Organic Spinach",
    description: "Fresh organic spinach leaves, perfect for salads",
    tags: ["vegetables", "leafy greens", "organic", "healthy"],
    imageUrl: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200&h=200&fit=crop"
  }
];

const SupermarketApp = () => {
  // State management
  const [currentPage, setCurrentPage] = useState('home');
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(mockItems);
  const [showPassword, setShowPassword] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    name: '', email: '', phone: '', address: '', password: '', creditCard: ''
  });
  const [editForm, setEditForm] = useState({});
  const [deliveryInfo, setDeliveryInfo] = useState({
    date: '', time: '', address: '', creditCard: ''
  });

  // Search functionality
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredItems(mockItems);
    } else {
      const filtered = mockItems.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      setFilteredItems(filtered);
    }
  }, [searchQuery]);

  // Cart functions
  const addToCart = (item) => {
    const existingItem = cart.find(cartItem => cartItem.id === item.id);
    if (existingItem) {
      setCart(cart.map(cartItem =>
        cartItem.id === item.id
          ? { ...cartItem, quantity: cartItem.quantity + 1 }
          : cartItem
      ));
    } else {
      setCart([...cart, { ...item, quantity: 1 }]);
    }
    sendAddDataToCartRequest(user.id, item).then()
  };

  const updateCartQuantity = (id, quantity) => {
    if (quantity <= 0) {
      setCart(cart.filter(item => item.id !== id));
    } else {
      setCart(cart.map(item =>
        item.id === id ? { ...item, quantity } : item
      ));
    }
  };

  const removeFromCart = (id) => {
    setCart(cart.filter(item => item.id !== id));
  };

  const generateCart = () => {
    // Simulate backend generating a cart
    const randomItems = mockItems.sort(() => 0.5 - Math.random()).slice(0, 3);
    const generatedCart = randomItems.map(item => ({ ...item, quantity: Math.floor(Math.random() * 3) + 1 }));
    setCart(generatedCart);
    alert('Cart generated with recommended items!');
  };

  // Auth functions
  const handleLogin = (e) => {
    e.preventDefault();
    // Mock login - in real app, this would make API call
    const mockUser = {
      name: 'John Doe',
      email: loginForm.email,
      phone: '+1-555-0123',
      address: '123 Main St, City, State 12345',
      creditCard: '****-****-****-1234'
    };
    setUser(mockUser);
    setCurrentPage('home');
    setLoginForm({ email: '', password: '' });
  };

  const handleRegister = (e) => {
    e.preventDefault();
    // Mock registration - in real app, would hash password and make API call
    const newUser = {
      name: registerForm.name,
      email: registerForm.email,
      phone: registerForm.phone,
      address: registerForm.address,
      creditCard: registerForm.creditCard.replace(/.(?=.{4})/g, '*')
    };
    setUser(newUser);
    setCurrentPage('home');
    setRegisterForm({
      name: '', email: '', phone: '', address: '', password: '', creditCard: ''
    });
  };

  const handleEditProfile = (e) => {
    e.preventDefault();
    setUser({ ...user, ...editForm });
    setCurrentPage('profile');
    setEditForm({});
  };

  const handleScheduleDelivery = (e) => {
    e.preventDefault();
    alert(`Delivery scheduled for ${deliveryInfo.date} at ${deliveryInfo.time}. Order will be delivered to: ${deliveryInfo.address}`);
    setCart([]);
    setCurrentPage('home');
    setDeliveryInfo({ date: '', time: '', address: '', creditCard: '' });
  };

  const logout = () => {
    setUser(null);
    setCart([]);
    setCurrentPage('home');
  };

  // Navigation
  const Navigation = () => (
    <nav className="bg-green-600 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold cursor-pointer" onClick={() => setCurrentPage('home')}>
          🛒 SuperMarket
        </h1>
        <div className="flex items-center space-x-6">
          <button
            onClick={() => setCurrentPage('home')}
            className={`hover:text-green-200 ${currentPage === 'home' ? 'text-green-200' : ''}`}
          >
            Home
          </button>
          <div className="relative">
            <button
              onClick={() => setCurrentPage('cart')}
              className={`flex items-center hover:text-green-200 ${currentPage === 'cart' ? 'text-green-200' : ''}`}
            >
              <ShoppingCart className="w-5 h-5 mr-1" />
              Cart ({cart.reduce((sum, item) => sum + item.quantity, 0)})
            </button>
          </div>
          {user ? (
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentPage('profile')}
                className={`flex items-center hover:text-green-200 ${currentPage === 'profile' ? 'text-green-200' : ''}`}
              >
                <User className="w-5 h-5 mr-1" />
                {user.name}
              </button>
              <button onClick={logout} className="hover:text-green-200">
                Logout
              </button>
            </div>
          ) : (
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentPage('login')}
                className={`hover:text-green-200 ${currentPage === 'login' ? 'text-green-200' : ''}`}
              >
                Login
              </button>
              <button
                onClick={() => setCurrentPage('register')}
                className={`hover:text-green-200 ${currentPage === 'register' ? 'text-green-200' : ''}`}
              >
                Register
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );

  // Home Page
  const HomePage = () => (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <div className="relative max-w-md mx-auto">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredItems.map(item => (
          <div key={item.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <img
              src={item.imageUrl}
              alt={item.name}
              className="w-full h-48 object-cover"
            />
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-2">{item.name}</h3>
              <p className="text-gray-600 text-sm mb-3">{item.description}</p>
              <div className="flex flex-wrap gap-1 mb-3">
                {item.tags.map(tag => (
                  <span key={tag} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                    {tag}
                  </span>
                ))}
              </div>
              <button
                onClick={() => addToCart(item)}
                className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add to Cart
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Cart Page
  const CartPage = () => (
    <div className="container mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Shopping Cart</h2>

      <div className="mb-6">
        <button
          onClick={generateCart}
          className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center"
        >
          <Star className="w-4 h-4 mr-2" />
          Generate Cart
        </button>
      </div>

      {cart.length === 0 ? (
        <div className="text-center py-12">
          <ShoppingCart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Your cart is empty</p>
        </div>
      ) : (
        <div className="space-y-4">
          {cart.map(item => (
            <div key={item.id} className="bg-white rounded-lg shadow-md p-4 flex items-center space-x-4">
              <img
                src={item.imageUrl}
                alt={item.name}
                className="w-16 h-16 object-cover rounded"
              />
              <div className="flex-1">
                <h3 className="font-semibold">{item.name}</h3>
                <p className="text-gray-600 text-sm">{item.description}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => updateCartQuantity(item.id, item.quantity - 1)}
                  className="p-1 rounded bg-gray-200 hover:bg-gray-300"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <span className="px-3 py-1 bg-gray-100 rounded">{item.quantity}</span>
                <button
                  onClick={() => updateCartQuantity(item.id, item.quantity + 1)}
                  className="p-1 rounded bg-gray-200 hover:bg-gray-300"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={() => removeFromCart(item.id)}
                  className="p-1 rounded bg-red-100 hover:bg-red-200 text-red-600 ml-2"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {user && (
            <div className="mt-8 bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Schedule Delivery</h3>
              <form onSubmit={handleScheduleDelivery} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Delivery Date</label>
                    <input
                      type="date"
                      value={deliveryInfo.date}
                      onChange={(e) => setDeliveryInfo({...deliveryInfo, date: e.target.value})}
                      required
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Delivery Time</label>
                    <select
                      value={deliveryInfo.time}
                      onChange={(e) => setDeliveryInfo({...deliveryInfo, time: e.target.value})}
                      required
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    >
                      <option value="">Select time</option>
                      <option value="9:00 AM - 12:00 PM">9:00 AM - 12:00 PM</option>
                      <option value="12:00 PM - 3:00 PM">12:00 PM - 3:00 PM</option>
                      <option value="3:00 PM - 6:00 PM">3:00 PM - 6:00 PM</option>
                      <option value="6:00 PM - 9:00 PM">6:00 PM - 9:00 PM</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Delivery Address</label>
                  <input
                    type="text"
                    value={deliveryInfo.address || user.address}
                    onChange={(e) => setDeliveryInfo({...deliveryInfo, address: e.target.value})}
                    placeholder="Enter delivery address"
                    required
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Payment Method</label>
                  <input
                    type="text"
                    value={deliveryInfo.creditCard || user.creditCard}
                    onChange={(e) => setDeliveryInfo({...deliveryInfo, creditCard: e.target.value})}
                    placeholder="Credit card ending in..."
                    required
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                >
                  <Calendar className="w-5 h-5 mr-2" />
                  Schedule Delivery
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Login Page
  const LoginPage = () => (
    <div className="container mx-auto p-6 max-w-md">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="email"
                value={loginForm.email}
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your email"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                required
                className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Login
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          Don't have an account?{' '}
          <button
            onClick={() => setCurrentPage('register')}
            className="text-green-600 hover:text-green-700 font-medium"
          >
            Register here
          </button>
        </p>
      </div>
    </div>
  );

  // Register Page
  const RegisterPage = () => (
    <div className="container mx-auto p-6 max-w-md">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Create Account</h2>
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={registerForm.name}
                onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your full name"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="email"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your email"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone Number</label>
            <div className="relative">
              <Phone className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="tel"
                value={registerForm.phone}
                onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your phone number"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Address</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={registerForm.address}
                onChange={(e) => setRegisterForm({...registerForm, address: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter your address"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Credit Card Number</label>
            <div className="relative">
              <CreditCard className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={registerForm.creditCard}
                onChange={(e) => setRegisterForm({...registerForm, creditCard: e.target.value})}
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Enter credit card number"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={registerForm.password}
                onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                required
                className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder="Create a password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Create Account
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          Already have an account?{' '}
          <button
            onClick={() => setCurrentPage('login')}
            className="text-green-600 hover:text-green-700 font-medium"
          >
            Login here
          </button>
        </p>
      </div>
    </div>
  );

  // Profile Page
  const ProfilePage = () => (
    <div className="container mx-auto p-6 max-w-2xl">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6">My Profile</h2>

        <div className="space-y-4 mb-8">
          <div className="flex items-center">
            <User className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <span className="font-medium">Name: </span>
              {user?.name}
            </div>
          </div>
          <div className="flex items-center">
            <Mail className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <span className="font-medium">Email: </span>
              {user?.email}
            </div>
          </div>
          <div className="flex items-center">
            <Phone className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <span className="font-medium">Phone: </span>
              {user?.phone}
            </div>
          </div>
          <div className="flex items-center">
            <MapPin className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <span className="font-medium">Address: </span>
              {user?.address}
            </div>
          </div>
          <div className="flex items-center">
            <CreditCard className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <span className="font-medium">Credit Card: </span>
              {user?.creditCard}
            </div>
          </div>
        </div>

        <button
          onClick={() => setCurrentPage('editProfile')}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Edit Profile
        </button>
      </div>
    </div>
  );

  // Edit Profile Page
  const EditProfilePage = () => (
    <div className="container mx-auto p-6 max-w-md">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Edit Profile</h2>
        <form onSubmit={handleEditProfile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Full Name</label>
            <input
              type="text"
              value={editForm.name || user?.name || ''}
              onChange={(e) => setEditForm({...editForm, name: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={editForm.email || user?.email || ''}
              onChange={(e) => setEditForm({...editForm, email: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone Number</label>
            <input
              type="tel"
              value={editForm.phone || user?.phone || ''}
              onChange={(e) => setEditForm({...editForm, phone: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Address</label>
            <input
              type="text"
              value={editForm.address || user?.address || ''}
              onChange={(e) => setEditForm({...editForm, address: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Credit Card Number</label>
            <input
              type="text"
              value={editForm.creditCard || user?.creditCard || ''}
              onChange={(e) => setEditForm({...editForm, creditCard: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="flex space-x-4">
            <button
              type="submit"
              className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              Save Changes
            </button>
            <button
              type="button"
              onClick={() => setCurrentPage('profile')}
              className="flex-1 bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // Render current page
  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage />;
      case 'cart':
        return <CartPage />;
      case 'login':
        return <LoginPage />;
      case 'register':
        return <RegisterPage />;
      case 'profile':
        return <ProfilePage />;
      case 'editProfile':
        return <EditProfilePage />;
      default:
        return <HomePage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      {renderCurrentPage()}
    </div>
  );
};

export default SupermarketApp;