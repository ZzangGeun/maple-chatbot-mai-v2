import React, { createContext, useContext, useReducer, useEffect } from 'react';
import * as authApi from '../api/auth';

const AuthContext = createContext();

// 로그인 응답과 세션 확인 응답의 프로필 위치를 같은 형태로 정규화합니다.
export const normalizeAuthUser = (payload) => {
  const account = payload.user || payload;
  return {
    ...account,
    maple_nickname: payload.maple_nickname
      ?? payload.profile?.maple_nickname
      ?? account.maple_nickname
      ?? account.profile?.maple_nickname
      ?? null,
  };
};

const initialState = {
  isLoggedIn: false,
  user: null,
  isLoading: true,
  isAuthReady: false,
  error: null,
  isLoginModalOpen: false,
  isSignupModalOpen: false, // 회원가입 모달 상태 추가
};

const authReducer = (state, action) => {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, isLoading: true, error: null };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isLoggedIn: true,
        isAuthReady: true,
        user: action.payload,
        isLoading: false,
        error: null,
        isLoginModalOpen: false,
        isSignupModalOpen: false,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        isLoggedIn: false,
        isAuthReady: true,
        user: null,
        isLoading: false,
        error: action.payload
      };
    case 'LOGOUT':
      return {
        ...state,
        isLoggedIn: false,
        isAuthReady: true,
        user: null,
        isLoading: false
      };
    case 'OPEN_LOGIN_MODAL':
      return { ...state, isLoginModalOpen: true, isSignupModalOpen: false, error: null };
    case 'CLOSE_LOGIN_MODAL':
      return { ...state, isLoginModalOpen: false, error: null };
    case 'OPEN_SIGNUP_MODAL':
      return { ...state, isSignupModalOpen: true, isLoginModalOpen: false, error: null };
    case 'CLOSE_SIGNUP_MODAL':
      return { ...state, isSignupModalOpen: false, error: null };
    case 'SIGNUP_SUCCESS':
      return { ...state, isSignupModalOpen: false, isLoading: false, error: null };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const checkAuth = async () => {
      dispatch({ type: 'AUTH_START' });
      try {
        const response = await authApi.getUserInfo();
        dispatch({ type: 'LOGIN_SUCCESS', payload: normalizeAuthUser(response.data) });
      } catch (error) {
        // 미로그인(401) 포함 모든 에러는 비로그인 상태로 처리
        dispatch({ type: 'LOGIN_FAILURE', payload: null });
      }
    };
    checkAuth();
  }, []);

  const login = async (username, password) => {
    dispatch({ type: 'AUTH_START' });
    try {
      const response = await authApi.login(username, password);
      dispatch({ type: 'LOGIN_SUCCESS', payload: normalizeAuthUser(response.data) });
      return { success: true };
    } catch (error) {
      let errorMessage = '로그인 실패';
      if (error.response && error.response.data) {
        const data = error.response.data;
        errorMessage = data.detail || data.error || data.message || '로그인 실패';
        if (typeof data === 'string') {
          try {
            const parsed = JSON.parse(data);
            errorMessage = parsed.detail || parsed.error || parsed.message || data;
          } catch (e) {
            errorMessage = data;
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const register = async (userData) => {
    dispatch({ type: 'AUTH_START' });
    try {
      await authApi.signup(userData);
      // 회원가입 성공 시 자동 로그인하지 않고 성공 반환
      dispatch({ type: 'SIGNUP_SUCCESS' });
      return { success: true, message: '회원가입이 완료되었습니다.' };
    } catch (error) {
      let errorMessage = '회원가입 실패';
      if (error.response && error.response.data) {
        const data = error.response.data;
        errorMessage = data.detail || data.error || data.message || '회원가입 실패';
        if (typeof data === 'string') {
          try {
            const parsed = JSON.parse(data);
            errorMessage = parsed.detail || parsed.error || parsed.message || data;
          } catch (e) {
            errorMessage = data;
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  const openLoginModal = () => dispatch({ type: 'OPEN_LOGIN_MODAL' });
  const closeLoginModal = () => dispatch({ type: 'CLOSE_LOGIN_MODAL' });
  const openSignupModal = () => dispatch({ type: 'OPEN_SIGNUP_MODAL' });
  const closeSignupModal = () => dispatch({ type: 'CLOSE_SIGNUP_MODAL' });

  const value = {
    ...state,
    login,
    logout,
    register,
    openLoginModal,
    closeLoginModal,
    openSignupModal,
    closeSignupModal,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
