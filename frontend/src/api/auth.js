import client from './client';

export const login = (username, password) => 
  client.post('/api/accounts/login/', { username, password });

export const logout = () => 
  client.post('/api/accounts/logout/');

export const signup = (userData) => 
  client.post('/api/accounts/signup/', userData);

export const getUserInfo = () => 
  client.get('/api/accounts/user/');
