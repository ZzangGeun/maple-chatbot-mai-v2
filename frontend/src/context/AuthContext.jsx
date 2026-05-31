import React, { createContext, useContext, useReducer, useEffect } from 'react';
import * as authApi from '../api/auth';

const AuthContext = createContext();

const initialState = {
  isLoggedIn: false,
  user: null,
  isLoading: true,
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
        user: null,
        isLoading: false,
        error: action.payload
      };
    case 'LOGOUT':
      return {
        ...state,
        isLoggedIn: false,
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
        // user_info 응답: { user: {id, username, email}, maple_nickname, message }
        // response.data 전체를 payload로 저장해 user.username, maple_nickname에 모두 접근 가능
        const response = await authApi.getUserInfo();
        dispatch({ type: 'LOGIN_SUCCESS', payload: response.data });
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
      dispatch({ type: 'LOGIN_SUCCESS', payload: response.data.user });
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
        error.response?.data?.error || 
        '로그인 실패';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const register = async (userData) => {
    dispatch({ type: 'AUTH_START' });
    try {
      const response = await authApi.signup(userData);
      // 회원가입 성공 시 자동 로그인하지 않고 성공 반환
      dispatch({ type: 'CLOSE_SIGNUP_MODAL' });
      return { success: true, message: '회원가입이 완료되었습니다.' };
    } catch (error) {
      const errorMessage = error.response?.data?.error ||
        error.response?.data?.message ||
        '회원가입 실패';
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