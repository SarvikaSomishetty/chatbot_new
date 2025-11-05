import React from 'react';
import { Moon, Sun, MessageCircle, BarChart3 } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useApp } from '../contexts/AppContext';
import ProfileDropdown from './ProfileDropdown';

interface HeaderProps {
  showProfile?: boolean;
}

const Header: React.FC<HeaderProps> = ({ showProfile = false }) => {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useApp();
  const kibanaUrl = (import.meta as any).env?.VITE_KIBANA_URL || 'http://localhost:5601';

  return (
    <header className="bg-white dark:bg-gray-900 shadow-lg border-b border-gray-100 dark:border-gray-700 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-teal-500 to-blue-600 p-2 rounded-xl shadow-lg shadow-teal-500/25">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              SupportHub
            </h1>
          </div>

          <div className="flex items-center space-x-3">
            <a
              href={kibanaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/30 transition-all duration-200 transform hover:scale-105"
              aria-label="Open Kibana dashboard"
              title="Open Kibana dashboard"
            >
              <BarChart3 className="w-5 h-5 text-teal-600 dark:text-teal-400" />
            </a>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 transform hover:scale-105"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              ) : (
                <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              )}
            </button>

            {showProfile && user && <ProfileDropdown />}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;