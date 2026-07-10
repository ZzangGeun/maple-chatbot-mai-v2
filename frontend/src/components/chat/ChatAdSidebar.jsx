import React from 'react';
import AdSense from '../common/AdSense';

const ChatAdSidebar = () => {
  return (
    <AdSense
      slotName="skyscraper"
      className="global-ad global-ad--skyscraper"
      style={{ minHeight: '600px' }}
    />
  );
};

export default ChatAdSidebar;
