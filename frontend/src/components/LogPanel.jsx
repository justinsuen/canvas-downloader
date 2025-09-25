import React from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

const LogPanel = ({ logs, setLogs }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 flex-1 flex flex-col min-h-0">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Download Log</h2>
        <button
          onClick={() => setLogs([])}
          className="text-sm text-gray-600 hover:text-gray-700"
        >
          Clear Log
        </button>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 overflow-y-auto flex-1 min-h-0">
        {logs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No activity yet</p>
        ) : (
          <div className="space-y-2">
            {logs.map((log, index) => (
              <div key={index} className="flex items-start gap-2 text-sm">
                <span className="text-gray-400 text-xs font-mono flex-shrink-0 mt-0.5">
                  {log.timestamp}
                </span>
                <div className="flex items-center gap-1 flex-1">
                  {log.type === 'error' && <AlertCircle size={14} className="text-red-500 flex-shrink-0" />}
                  {log.type === 'warning' && <AlertCircle size={14} className="text-yellow-500 flex-shrink-0" />}
                  {log.type === 'success' && <CheckCircle size={14} className="text-green-500 flex-shrink-0" />}
                  <span className={`${log.type === 'error' ? 'text-red-700' :
                    log.type === 'warning' ? 'text-yellow-700' :
                      log.type === 'success' ? 'text-green-700' :
                        'text-gray-700'
                    }`}>
                    {log.message}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogPanel;