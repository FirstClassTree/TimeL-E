import { api } from './api.client';

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

class UserService {
  // Get user profile
  async getProfile(userId: string): Promise<UserProfile> {
    return api.get<UserProfile>(`/users/${userId}`);
  }

  // Update user profile
  async updateProfile(userId: string, data: UpdateProfileRequest): Promise<UserProfile> {
    return api.put<UserProfile>(`/users/${userId}`, data);
  }

  // Change user password
  async changePassword(userId: string, data: ChangePasswordRequest): Promise<void> {
    return api.put<void>(`/users/${userId}/password`, data);
  }

  // Get user preferences
  async getPreferences(userId: string): Promise<any> {
    return api.get(`/users/${userId}/preferences`);
  }

  // Update user preferences
  async updatePreferences(userId: string, preferences: any): Promise<any> {
    return api.put(`/users/${userId}/preferences`, preferences);
  }

  // Delete user
  async deleteAccount(userId: string): Promise<void> {
    return api.delete(`/users/${userId}`);
  }

  // Get user statistics
  async getStats(): Promise<any> {
    return api.get('/users/stats');
  }
}

// Export as singleton instance to match your import pattern
export const userService = new UserService();