import client from './client';

export const login = (username, password) => 
  client.post('/api/v1/accounts/login/', { username, password });

export const logout = () => 
  client.post('/api/v1/accounts/logout/');

export const signup = (userData) => 
  client.post('/api/v1/accounts/signup/', userData);

export const getUserInfo = () => 
  client.get('/api/v1/accounts/user/');
