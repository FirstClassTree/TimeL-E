import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { authService, RegisterData, User} from '@/services/auth.service';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    emailAddress: string;
    password: string;
    firstName: string;
    lastName: string;
    phoneNumber?: string;
    streetAddress?: string;
    city?: string;
    postalCode?: string;
    country?: string;
    daysBetweenOrderNotifications?: number;
    orderNotificationsViaEmail?: boolean;
    orderNotificationsStartDateTime?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  updateUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
    devtools(
        persist(
            (set, get) => ({
              user: authService.getUser(),
              isAuthenticated: authService.isAuthenticated(),
              isLoading: false,

              login: async (emailAddress, password) => {
                set({isLoading: true});
                try {
                  const response = await authService.login({emailAddress, password});
                  set({
                    user: response.user,
                    isAuthenticated: true,
                    isLoading: false
                  });
                  toast.success(`Welcome back, ${response.user.firstName} ${response.user.lastName}!`);
                } catch (error: any) {
                  set({isLoading: false});
                  throw error;
                }
              },

              register: async (data: RegisterData) => {
          set({ isLoading: true });
          try {
            const response = await authService.register(data);
            set({
              user: response.user,
              isAuthenticated: true,
              isLoading: false
            });
            toast.success('Account created successfully!');
          } catch (error: any) {
            set({ isLoading: false });
            throw error;
          }
        },

        logout: async () => {
          set({ isLoading: true });
          try {
            await authService.logout();
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false
            });
            toast.success('Logged out successfully');
          } catch (error) {
            // Even if logout fails, clear local state
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false
            });
          }
        },

        refreshAuth: async () => {
          try {
            const user = await authService.getCurrentUser();
            set({
              user,
              isAuthenticated: true
            });
          } catch (error) {
            set({
              user: null,
              isAuthenticated: false
            });
          }
        },

        updateUser: (user) => {
          set({ user });
        },

        clearAuth: () => {
          set({
            user: null,
            isAuthenticated: false
          });
        }
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated
        })
      }
    ),
    {
      name: 'auth-store'
    }
  )
);