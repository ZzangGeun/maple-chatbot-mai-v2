import client from './client';

export const getHomeData = () => 
  client.get('/api/v1/core/home/data/');

export const searchCharacter = (name) =>
  client.get('/api/v1/character/search/', { params: { name: name } });
