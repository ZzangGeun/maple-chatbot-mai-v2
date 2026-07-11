import React from 'react';
import AdSense from '../common/AdSense';

const AdSidebar = () => {
    return (
        <aside className="sidebar-right">
            <AdSense
                slotName="skyscraper"
                className="global-ad global-ad--skyscraper"
                style={{ minHeight: '600px' }}
            />
        </aside>
    );
};

export default AdSidebar;
