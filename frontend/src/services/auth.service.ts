import { api } from '@/services/api.client';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  firstName: string;
  lastName: string;
  emailAddress: string;
  password: string;
  phoneNumber?: string;
  streetAddress?: string;
  city?: string;
  postalCode?: string;
  country?: string;
  daysBetweenOrderNotifications?: number;
  orderNotificationsViaEmail?: boolean;
  orderNotificationsStartDateTime?: string;
}

interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

interface User {
  userId: string;
  firstName: string;
  lastName: string;
  emailAddress: string;
  phoneNumber: string;
}

class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'timele_access_token';
  private readonly REFRESH_TOKEN_KEY = 'timele_refresh_token';
  private readonly USER_KEY = 'timele_user';

  // Login - Adapted for demo backend
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Call the demo login endpoint (GET request, ignores credentials)
    const response = await api.get('/users/login');
    
    // Transform backend format to frontend expected format
    const user = {
      id: response.userId,
      firstName: response.firstName,
      lastName: response.lastName,
      emailAddress: response.emailAddress,
      phoneNumber: response.phoneNumber
    };
    
    // Create mock tokens since backend doesn't provide them
    const mockAuth = {
      user,
      accessToken: `demo_token_${response.userId}`,
      refreshToken: `demo_refresh_${response.userId}`
    };
    
    this.setTokens(mockAuth.accessToken, mockAuth.refreshToken);
    this.setUser(mockAuth.user);
    
    return mockAuth;
  }

  // Register
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/users/register', data);
    this.setTokens(response.accessToken, response.refreshToken);
    this.setUser(response.user);
    return response;
  }

  // Logout
  async logout(): Promise<void> {
    try {
      await api.post('/users/logout');
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.clearAuth();
    }
  }

  // Refresh token
  async refreshToken(): Promise<void> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post<{ accessToken: string; refreshToken: string }>(
      '/users/refresh',
      { refreshToken }
    );

    this.setTokens(response.accessToken, response.refreshToken);
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await api.get<{ user: User }>('/auth/me');
    this.setUser(response.user);
    return response.user;
  }

  // Forgot password
  async forgotPassword(email: string): Promise<void> {
    await api.post('/users/forgot-password', { email });
  }

  // Reset password
  async resetPassword(userId: string, token: string, password: string): Promise<void> {
    await api.post(`/users/${userId}/reset-password`, { token, password });
  }

  // Token management
  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  // User management
  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  private setUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !!this.getUser();
  }

  // Clear auth data
  private clearAuth(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }
}

export const authService = new AuthService();
export type { User, LoginCredentials, RegisterData, AuthResponse };
