import React from 'react';
import AdSense from '../common/AdSense';

const AdSidebar = () => {
    return (
        <aside className="sidebar-right">
            <div className="sidebar-ad-container" style={{ width: '100%', height: '100%', minHeight: '350px', background: '#f8f9fa', borderRadius: '15px', overflow: 'hidden' }}>
                <AdSense slot="YOUR_SIDEBAR_SLOT_ID" style={{ display: 'block', width: '100%', height: '100%' }} />
            </div>
        </aside>
    );
};

export default AdSidebar;
