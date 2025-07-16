// frontend/src/services/user.service.ts
import { apiClient } from './api.client';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  preferences?: any;
}

export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export const userService = {
  // Get current user profile
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/users/profile');
    return response.data;
  },

  // Update user profile
  updateProfile: async (data: UpdateProfileRequest): Promise<UserProfile> => {
    const response = await apiClient.put('/users/profile', data);
    return response.data;
  },

  // Change user password
  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await apiClient.put('/users/password', data);
  },

  // Get user preferences
  getPreferences: async (): Promise<any> => {
    const response = await apiClient.get('/users/preferences');
    return response.data;
  },

  // Update user preferences
  updatePreferences: async (preferences: any): Promise<any> => {
    const response = await apiClient.put('/users/preferences', preferences);
    return response.data;
  },

  // Delete user account
  deleteAccount: async (): Promise<void> => {
    await apiClient.delete('/users/profile');
  },

  // Get user statistics
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/users/stats');
    return response.data;
  }
};

export default userService;
