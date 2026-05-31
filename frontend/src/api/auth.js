import client from './client';

export const login = (username, password) => 
  client.post('/api/v1/auth/login/', { username, password });

export const logout = () => 
  client.post('/api/v1/auth/logout/');

export const signup = (userData) => 
  client.post('/api/v1/auth/signup/', userData);

export const getUserInfo = () => 
  client.get('/api/v1/auth/user/');

