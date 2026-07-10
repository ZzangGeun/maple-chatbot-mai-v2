import client from './client';

export const getCommunityPosts = (params) =>
  client.get('/api/v1/community/posts/', { params });

export const createCommunityPost = (post) =>
  client.post('/api/v1/community/posts/', post);