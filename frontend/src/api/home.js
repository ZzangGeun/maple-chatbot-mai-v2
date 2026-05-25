import client from './client';

export const getHomeData = () => 
  client.get('/api/core/home/data/');

export const searchCharacter = (name) =>
  client.get('/api/character/search/', { params: { name: name } });
