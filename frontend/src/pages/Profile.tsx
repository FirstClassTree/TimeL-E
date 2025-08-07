import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User, Mail, Settings,
  Edit3, Save, X, CheckCircle, Eye, EyeOff, Phone
} from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import { userService } from '@/services/user.service';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import toast from 'react-hot-toast';

interface ProfileFormData {
  userId: string;
  firstName: string;
  lastName: string;
  emailAddress: string;
  phoneNumber?: string;
}

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const Profile: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Create a mock user if none exists
  const currentUser = user || {
    userId: '8450d218-5822-55af-8818-961027c51a6e',
    firstName: 'Demo',
    lastName: 'User',
    emailAddress: 'demo@example.com',
    phoneNumber: '+555 555 5550'
  };

  const {
    register: registerProfile,
    handleSubmit: handleSubmitProfile,
    formState: { errors: profileErrors },
    reset: resetProfile
  } = useForm<ProfileFormData>({
    defaultValues: {
      userId: currentUser.userId,
      firstName: currentUser.firstName,
      lastName: currentUser.lastName,
      emailAddress: currentUser.emailAddress,
      phoneNumber: currentUser.phoneNumber
    }
  });

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    formState: { errors: passwordErrors },
    reset: resetPassword,
    watch
  } = useForm<PasswordFormData>();

  // Update profile mutation
  const updateProfileMutation = useMutation(
        ({ id, data }: { id: string; data: any }) =>
    userService.updateProfile(id, data),
  {
    onSuccess: (data) => {
      updateUser(data);
      setIsEditing(false);
      queryClient.invalidateQueries(['user-profile']);
      toast.success('Profile updated successfully! 🎉');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.message || 'Failed to update profile';
      toast.error(errorMessage);
    }
  });

  // Change password mutation
  const changePasswordMutation = useMutation(
        ({ id, passwordData }: { id: string; passwordData: any }) =>
    userService.changePassword(id, passwordData),
  {
    onSuccess: () => {
      setShowPasswordForm(false);
      resetPassword();
      toast.success('Password changed successfully! 🔒');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.message || 'Failed to change password';
      toast.error(errorMessage);
    }
  });

  const onSubmitProfile = (data: ProfileFormData) => {
    let id = user?.userId;
    updateProfileMutation.mutate({id, data});
  };

  const onSubmitPassword = (data: PasswordFormData) => {
    if (data.newPassword !== data.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    let id = user?.userId;
    changePasswordMutation.mutate({
      id : id,
      passwordData:  {
      currentPassword: data.currentPassword,
      newPassword: data.newPassword
    }});
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    resetProfile({
      userId: currentUser.userId,
      firstName: currentUser.firstName,
      lastName: currentUser.lastName,
      emailAddress: currentUser.emailAddress,
      phoneNumber: currentUser.phoneNumber
    });
  };

  // Always render the profile page now since we have currentUser fallback

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Profile</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your account information
          </p>
        </div>

        <div className="space-y-8">
          
          {/* Profile Information Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-xl">
                      {currentUser.firstName?.charAt(0)}{currentUser.lastName?.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {currentUser.firstName} {currentUser.lastName}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">{currentUser.emailAddress}</p>
                  </div>
                </div>
                
                {!isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-md hover:bg-cyan-700 transition-colors"
                  >
                    <Edit3 size={16} />
                    Edit Profile
                  </button>
                )}
              </div>
            </div>

            <form onSubmit={handleSubmitProfile(onSubmitProfile)} className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    First Name
                  </label>
                  {isEditing ? (
                      <input
                          type="text"
                          {...registerProfile('firstName', {required: 'First Name is required'})}
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                  ) : (
                      <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                        <User size={16} className="text-gray-500 dark:text-gray-400"/>
                        <span className="text-gray-900 dark:text-white">{currentUser.firstName}</span>
                      </div>
                  )}
                  {profileErrors.firstName && (
                      <p className="text-red-500 text-sm mt-1">{profileErrors.firstName.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Last Name
                  </label>
                  {isEditing ? (
                      <input
                          type="text"
                          {...registerProfile('lastName', {required: 'Last name is required'})}
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                  ) : (
                      <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                        <User size={16} className="text-gray-500 dark:text-gray-400"/>
                        <span className="text-gray-900 dark:text-white">{currentUser.lastName}</span>
                      </div>
                  )}
                  {profileErrors.lastName && (
                      <p className="text-red-500 text-sm mt-1">{profileErrors.lastName.message}</p>
                  )}
                </div>


                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email Address
                  </label>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <Mail size={16} className="text-gray-500 dark:text-gray-400"/>
                    <span className="text-gray-900 dark:text-white">{currentUser.emailAddress}</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Email cannot be changed in demo mode
                  </p>
                </div>

               {/* Phone Number */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Phone Number
                  </label>
                  {isEditing ? (
                    <input
                      type="tel"
                      {...registerProfile('phoneNumber')}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Optional"
                    />
                  ) : (
                    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                      <Phone size={16} className="text-gray-500 dark:text-gray-400" />
                      <span className="text-gray-900 dark:text-white">
                        {currentUser.phoneNumber || 'Not provided'}
                      </span>
                    </div>
                  )}
                </div>
             </div>

              {/* Action Buttons */}
              <AnimatePresence>
                {isEditing && (
                    <motion.div
                        initial={{opacity: 0, height: 0}}
                        animate={{opacity: 1, height: 'auto'}}
                        exit={{opacity: 0, height: 0}}
                        className="flex justify-end gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-gray-700"
                    >
                      <button
                          type="button"
                          onClick={handleCancelEdit}
                          className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <X size={16}/>
                        Cancel
                      </button>
                      <button
                          type="submit"
                          disabled={updateProfileMutation.isLoading}
                          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-md hover:bg-cyan-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {updateProfileMutation.isLoading ? (
                        <>
                          <LoadingSpinner size="small" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save size={16} />
                          Save Changes
                        </>
                      )}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </form>
          </div>

          {/* Password Change Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Password & Security
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Update your password to keep your account secure
                  </p>
                </div>
                
                {!showPasswordForm && (
                  <button
                    onClick={() => setShowPasswordForm(true)}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Settings size={16} />
                    Change Password
                  </button>
                )}
              </div>
            </div>

            <AnimatePresence>
              {showPasswordForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="p-6"
                >
                  <form onSubmit={handleSubmitPassword(onSubmitPassword)} className="space-y-6">
                    
                    {/* Current Password */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Current Password
                      </label>
                      <div className="relative">
                        <input
                          type={showCurrentPassword ? 'text' : 'password'}
                          {...registerPassword('currentPassword', { required: 'Current password is required' })}
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400"
                        >
                          {showCurrentPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                      {passwordErrors.currentPassword && (
                        <p className="text-red-500 text-sm mt-1">{passwordErrors.currentPassword.message}</p>
                      )}
                    </div>

                    {/* New Password */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        New Password
                      </label>
                      <div className="relative">
                        <input
                          type={showNewPassword ? 'text' : 'password'}
                          {...registerPassword('newPassword', { 
                            required: 'New password is required',
                            minLength: {
                              value: 6,
                              message: 'Password must be at least 6 characters'
                            }
                          })}
                          className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400"
                        >
                          {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                      {passwordErrors.newPassword && (
                        <p className="text-red-500 text-sm mt-1">{passwordErrors.newPassword.message}</p>
                      )}
                    </div>

                    {/* Confirm Password */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        {...registerPassword('confirmPassword', { 
                          required: 'Please confirm your new password',
                          validate: value => 
                            value === watch('newPassword') || 'Passwords do not match'
                        })}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                      {passwordErrors.confirmPassword && (
                        <p className="text-red-500 text-sm mt-1">{passwordErrors.confirmPassword.message}</p>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
                      <button
                        type="button"
                        onClick={() => {
                          setShowPasswordForm(false);
                          resetPassword();
                        }}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <X size={16} />
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={changePasswordMutation.isLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-md hover:bg-cyan-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {changePasswordMutation.isLoading ? (
                          <>
                            <LoadingSpinner size="small" />
                            Updating...
                          </>
                        ) : (
                          <>
                            <CheckCircle size={16} />
                            Update Password
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Account Information */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Account Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Last Login</p>
                <p className="text-gray-900 dark:text-white mt-1">
                  {user.lastLogin
                      ? new Date(user.lastLogin).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })
                      : 'This is your first time here!'
                  }
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Profile;
