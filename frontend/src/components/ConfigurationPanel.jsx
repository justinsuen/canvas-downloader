import React from 'react';

const ConfigurationPanel = ({ config, setConfig, setShowConfig, sendToLogPanel, onSave }) => {
  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <h2 className="text-xl font-semibold mb-4">Configuration</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Canvas API URL</label>
          <input
            type="text"
            placeholder="https://your-school.instructure.com"
            value={config.apiUrl}
            onChange={(e) => setConfig({ ...config, apiUrl: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
          <input
            type="text"
            placeholder="Your Canvas API token"
            value={config.apiKey}
            onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoComplete="off"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Output Directory</label>
          <input
            type="text"
            placeholder="./downloads"
            value={config.outputPath}
            onChange={(e) => setConfig({ ...config, outputPath: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setShowConfig(false);
              sendToLogPanel('Configuration updated successfully', 'success');
              // Trigger course fetching after saving
              if (onSave) {
                onSave();
              }
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Authenticate and Fetch Courses
          </button>
          <button
            onClick={() => setShowConfig(false)}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPanel;