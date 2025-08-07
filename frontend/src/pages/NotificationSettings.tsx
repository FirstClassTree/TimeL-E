import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Bell, Clock, Mail, Save, Check } from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import { userService } from '@/services/user.service';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const NotificationSettings: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    daysBetweenOrderNotifications: 7,
    orderNotificationsStartDateTime: '',
    orderNotificationsViaEmail: true
  });

  useEffect(() => {
    loadSettings();
  }, [user?.userId]);

  const loadSettings = async () => {
    if (!user?.userId) return;
    
    try {
      setLoading(true);
      const userSettings = await userService.getNotificationSettings(user.userId);
      setSettings({
        daysBetweenOrderNotifications: userSettings.daysBetweenOrderNotifications,
        orderNotificationsStartDateTime: userSettings.orderNotificationsStartDateTime,
        orderNotificationsViaEmail: userSettings.orderNotificationsViaEmail
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load notification settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!user?.userId) return;

    try {
      setSaving(true);
      await userService.updateNotificationSettings(user.userId, settings);
      toast.success('Notification settings updated successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeft size={20} />
            Back
          </button>
          
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Notification Settings
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-300">
            Configure when and how you want to receive shopping reminders
          </p>
        </div>

        {/* Settings Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="space-y-8">
            {/* Frequency Setting */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-3">
                <Clock className="inline w-5 h-5 mr-2" />
                Notification Frequency
              </label>
              <select
                value={settings.daysBetweenOrderNotifications}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  daysBetweenOrderNotifications: parseInt(e.target.value)
                }))}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>Daily</option>
                <option value={3}>Every 3 days</option>
                <option value={7}>Weekly</option>
                <option value={14}>Every 2 weeks</option>
                <option value={30}>Monthly</option>
              </select>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                How often would you like to receive shopping reminders?
              </p>
            </div>

            {/* Start Date/Time Setting */}
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-3">
                Start Date & Time
              </label>
              <input
                type="datetime-local"
                value={settings.orderNotificationsStartDateTime}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  orderNotificationsStartDateTime: e.target.value
                }))}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                When should we start sending you notifications?
              </p>
            </div>

            {/* Email Notifications Toggle */}
            <div>
              <label className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Email Notifications
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Receive notifications via email
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={settings.orderNotificationsViaEmail}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      orderNotificationsViaEmail: e.target.checked
                    }))}
                    className="sr-only"
                  />
                  <div
                    onClick={() => setSettings(prev => ({
                      ...prev,
                      orderNotificationsViaEmail: !prev.orderNotificationsViaEmail
                    }))}
                    className={`w-12 h-6 rounded-full cursor-pointer transition-colors ${
                      settings.orderNotificationsViaEmail
                        ? 'bg-blue-600'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                        settings.orderNotificationsViaEmail
                          ? 'translate-x-6'
                          : 'translate-x-0.5'
                      }`}
                      style={{ marginTop: '2px' }}
                    />
                  </div>
                </div>
              </label>
            </div>

            {/* Preview Section */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Preview
              </h3>
              <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <p>
                  <strong>Frequency:</strong> Every {settings.daysBetweenOrderNotifications} day{settings.daysBetweenOrderNotifications !== 1 ? 's' : ''}
                </p>
                {settings.orderNotificationsStartDateTime && (
                  <p>
                    <strong>Starting:</strong> {new Date(settings.orderNotificationsStartDateTime).toLocaleString()}
                  </p>
                )}
                <p>
                  <strong>Via Email:</strong> {settings.orderNotificationsViaEmail ? 'Yes' : 'No'}
                </p>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex gap-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <Save size={20} />
                )}
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
              
              <button
                onClick={() => navigate('/')}
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        {/* Success Message */}
        <div className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
            <Check size={20} />
            <span className="font-semibold">All set!</span>
          </div>
          <p className="text-sm text-green-600 dark:text-green-400 mt-1">
            Your notification preferences will be applied to future shopping reminders.
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;
