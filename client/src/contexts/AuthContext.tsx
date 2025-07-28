import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { checkLoginStatus, logoutUser } from '../utils/api';

interface AuthContextType {
  isLoggedIn: boolean;
  participantId: string;
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
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [participantId, setParticipantId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkLogin = async () => {
      try {
        const { isLoggedIn: loggedIn, participantId: id } = await checkLoginStatus();
        setIsLoggedIn(loggedIn);
        if (id) {
          setParticipantId(id);
        }
      } catch (error) {
        console.error('Error checking login status:', error);
        setIsLoggedIn(false);
        setParticipantId('');
      } finally {
        setIsLoading(false);
      }
    };
    checkLogin();
  }, []);

  const login = (id: string) => {
    setIsLoggedIn(true);
    setParticipantId(id);
  };

  const logout = async () => {
    try {
      await logoutUser();
      setIsLoggedIn(false);
      setParticipantId('');
    } catch (error) {
      console.error('Error logging out:', error);
      // Still update local state even if API call fails
      setIsLoggedIn(false);
      setParticipantId('');
    }
  };

  const value = {
    isLoggedIn,
    participantId,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};