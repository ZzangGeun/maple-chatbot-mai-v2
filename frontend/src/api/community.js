import client from './client';

export const getPosts = async (category = 'all', sortBy = 'latest', page = 1, limit = 20) => {
    try {
        const response = await client.get('/community/posts', {
            params: {
                category,
                sort_by: sortBy,
                page,
                limit
            }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to fetch posts:', error);
        throw error;
    }
};

export const getPost = async (postId) => {
    try {
        const response = await client.get(`/community/posts/${postId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch post:', error);
        throw error;
    }
};

export const createPost = async (postData) => {
    try {
        const response = await client.post('/community/posts', postData);
        return response.data;
    } catch (error) {
        console.error('Failed to create post:', error);
        throw error;
    }
};

export const updatePost = async (postId, postData) => {
    try {
        const response = await client.put(`/community/posts/${postId}`, postData);
        return response.data;
    } catch (error) {
        console.error('Failed to update post:', error);
        throw error;
    }
};

export const deletePost = async (postId) => {
    try {
        const response = await client.delete(`/community/posts/${postId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to delete post:', error);
        throw error;
    }
};

export const getComments = async (postId, page = 1, limit = 50) => {
    try {
        const response = await client.get(`/community/posts/${postId}/comments`, {
            params: {
                page,
                limit
            }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to fetch comments:', error);
        throw error;
    }
};

export const createComment = async (postId, commentData) => {
    try {
        const response = await client.post(`/community/posts/${postId}/comments`, commentData);
        return response.data;
    } catch (error) {
        console.error('Failed to create comment:', error);
        throw error;
    }
};

export const updateComment = async (postId, commentId, commentData) => {
    try {
        const response = await client.put(`/community/posts/${postId}/comments/${commentId}`, commentData);
        return response.data;
    } catch (error) {
        console.error('Failed to update comment:', error);
        throw error;
    }
};

export const deleteComment = async (postId, commentId) => {
    try {
        const response = await client.delete(`/community/posts/${postId}/comments/${commentId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to delete comment:', error);
        throw error;
    }
};

export const likePost = async (postId) => {
    try {
        const response = await client.post(`/community/posts/${postId}/like`);
        return response.data;
    } catch (error) {
        console.error('Failed to like post:', error);
        throw error;
    }
};

export const unlikePost = async (postId) => {
    try {
        const response = await client.delete(`/community/posts/${postId}/like`);
        return response.data;
    } catch (error) {
        console.error('Failed to unlike post:', error);
        throw error;
    }
};

export const searchPosts = async (query, category = 'all', sortBy = 'latest', page = 1, limit = 20) => {
    try {
        const response = await client.get('/community/search', {
            params: {
                q: query,
                category,
                sort_by: sortBy,
                page,
                limit
            }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to search posts:', error);
        throw error;
    }
};

export const getCategories = async () => {
    try {
        const response = await client.get('/community/categories');
        return response.data;
    } catch (error) {
        console.error('Failed to fetch categories:', error);
        throw error;
    }
};

export const getMyPosts = async (page = 1, limit = 20) => {
    try {
        const response = await client.get('/community/my/posts', {
            params: {
                page,
                limit
            }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to fetch my posts:', error);
        throw error;
    }
};

export const getMyComments = async (page = 1, limit = 20) => {
    try {
        const response = await client.get('/community/my/comments', {
            params: {
                page,
                limit
            }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to fetch my comments:', error);
        throw error;
    }
};