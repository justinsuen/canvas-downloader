import React from 'react';
import { Download, Settings, Wifi, WifiOff } from 'lucide-react';

const Header = ({ showConfig, setShowConfig, backendConnected, isConnected, currentUser }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Download className="text-blue-600" />
            Canvas Sync
          </h1>
          <div className="flex items-center gap-4 mt-2">
            <p className="text-gray-600">
              Sync and download all your Canvas course files automatically
            </p>
            {currentUser && (
              <span className="text-sm text-green-700 bg-green-100 px-2 py-1 rounded">
                Logged in as {currentUser.name}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Backend Status Indicator */}
          <div className="flex items-center gap-2">
            {backendConnected && currentUser ? (
              <div className="flex items-center gap-1 text-green-600">
                <Wifi size={16} />
                <span className="text-xs">Connected</span>
              </div>
            ) : isConnected ? (
              <div className="flex items-center gap-1 text-blue-600">
                <Wifi size={16} />
                <span className="text-xs">Ready to Connect</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-orange-600">
                <WifiOff size={16} />
                <span className="text-xs">Demo Mode</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Settings size={16} />
            Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default Header;