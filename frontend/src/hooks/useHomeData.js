import { useState, useEffect } from 'react';
import * as homeApi from '../api/home';

export const useHomeData = () => {
    const [homeData, setHomeData] = useState({
        notices: { updates: [], events: [], cashshop: [] },
        ranking: []
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                const response = await homeApi.getHomeData();
                setHomeData(response.data);
            } catch (err) {
                console.error("Failed to fetch home data:", err);
                setError(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    return { homeData, isLoading, error };
};
