import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { checkLoginStatus, logoutUser } from '../utils/api';

export interface User {
  id: string;
  // Add other user properties here if needed in the future
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (id: string) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkLogin = async () => {
      try {
        const { isLoggedIn: loggedIn, participantId } = await checkLoginStatus();
        if (loggedIn && participantId) {
          setUser({ id: participantId });
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Error checking login status:', error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    checkLogin();
  }, []);

  const login = (id: string) => {
    setUser({ id });
    // Also set in session storage for persistence across reloads
    sessionStorage.setItem('user_id', id);
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.error('Error logging out:', error);
    } finally {
      setUser(null);
      sessionStorage.removeItem('user_id');
    }
  };

  const value = {
    user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};