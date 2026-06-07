export const getCategoryIcon = (categoryId) => {
    const icons = {
        free: '💬',
        question: '❓',
        guide: '📖',
        trade: '💰',
        guild: '🏰'
    };
    return icons[categoryId] || '📄';
};
