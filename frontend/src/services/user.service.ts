import { apiClient } from './api.client';
import { useUser } from '@/components/auth/UserProvider';

const { setUserId } = useUser();

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
  name: string;
}

export interface UpdateProfileRequest {
  name?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export const userService = {
  // Get user profile
  getProfile: async (userId : string): Promise<UserProfile> => {
    const response = await apiClient.get(`/users/${userId}`);
    setUserId(response.data.id);
    return response.data;
  },

  // Update user profile
  updateProfile: async(userId: string, data: UpdateProfileRequest): Promise<UserProfile> => {
    const response = await apiClient.put(`/users/${userId}`, data);
    return response.data;
  },

  // Change user password
  changePassword: async (userId: string ,data: ChangePasswordRequest): Promise<void> => {
    await apiClient.put(`/users/${userId}/password`, data);
  },

  // Get user preferences
  getPreferences: async (userId: string): Promise<any> => {
    const response = await apiClient.get(`/users/${userId}/preferences`);
    return response.data;
  },

  // Update user preferences
  updatePreferences: async (userId: string ,preferences: any): Promise<any> => {
    const response = await apiClient.put(`/users/${userId}/preferences`, preferences);
    return response.data;
  },

  // Delete user
  deleteAccount: async (userId: string): Promise<void> => {
    await apiClient.delete(`/users/${userId}`);
  },

  // Get user statistics
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/users/stats');
    return response.data;
  }
};

export default userService;
