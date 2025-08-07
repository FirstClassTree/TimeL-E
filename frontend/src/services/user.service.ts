import { api } from './api.client';

export interface UserProfile {
  userId: string;
  firstName: string;
  lastName: string;
  emailAddress: string;
  phoneNumber: string;
  streetAddress: string;
  city: string;
  postalCode: string;
  country: string;
  daysBetweenOrderNotifications: number;
  orderNotificationsStartDateTime: string;
  orderNotificationsNextScheduledTime: string
  pendingOrderNotification: boolean;
  orderNotificationsViaEmail: boolean;
  lastNotificationSentAt: string;
  lastLogin: string;
  lastNotificationsViewedAt: string;
  hasActiveCart: boolean;
}

export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface ChangePasswordResponse {
  userId: string;
  passwordUpdated: string;
}

export interface ChangeEmailRequest {
  currentPassword: string;
  newEmailAddress: string;
}

export interface DeleteUserRequest {
  password: string;
}

export  interface UpdateNotificationSettingsRequest {
  daysBetweenOrderNotifications: number;
  orderNotificationsStartDateTime: string;
  orderNotificationsViaEmail: boolean;
}

export interface NotificationSettings {
  userId: string;
  daysBetweenOrderNotifications: number;
  orderNotificationsStartDateTime: string;
  orderNotificationsNextScheduledTime?: string;
  pendingOrderNotification?: boolean;
  orderNotificationsViaEmail: boolean;
  lastNotificationSentAt?: string;
}

export  interface UpdateNotificationSettingsResponse {
  userId: string;
  daysBetweenOrderNotifications: number;
  orderNotificationsStartDateTime: string;
  orderNotificationsViaEmail: boolean;
  orderNotificationsNextScheduledTime: string;
}

export interface GetAllOrderNotificationsRequest {
  notifications: OrderNotification[];
}

export interface OrderNotification {
  orderId: number;
  status: 'PENDING' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  changedAt: string;
}

class UserService {
  // Get user profile
  async getProfile(userId: string): Promise<UserProfile> {
    return api.post<UserProfile>(`/users/${userId}`);
  }

  // Update user profile
  async updateProfile(userId: string, data: UpdateProfileRequest): Promise<UserProfile> {
    return api.put<UserProfile>(`/users/${userId}`, data);
  }

  // Change user password
  async changePassword(userId: string, data: ChangePasswordRequest): Promise<ChangePasswordResponse> {
    return api.put<ChangePasswordResponse>(`/users/${userId}/password`, data);
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
  async deleteAccount(userId: string, data: DeleteUserRequest): Promise<void> {
    return api.delete(`/users/${userId}`, data);
  }

  // Get notification settings
  async getNotificationSettings(userId: string): Promise<NotificationSettings> {
    return api.get(`/users/${userId}/notification-settings`);
  }

  //Update Notification Settings
  async updateNotificationSettings(userId : string, data: UpdateNotificationSettingsRequest) : Promise<UpdateNotificationSettingsResponse> {
    return api.put(`/users/${userId}/notification-settings`, data)
  }

  //Update Email
  async updateEmail(userId : string, data: ChangeEmailRequest) : Promise<void> {
    return api.put(`/users/${userId}/email`, data)
  }

    async GetOrderNotifications(userId: string, data: GetAllOrderNotificationsRequest) : Promise<void> {
        return api.put(`/users/${userId}/order-status-notifications`, data)
    }
}

export const userService = new UserService();
