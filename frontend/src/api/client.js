import axios from 'axios';

export function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const client = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

client.interceptors.request.use(
  (config) => {
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
      config.headers['X-CSRFToken'] = csrftoken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default client;
