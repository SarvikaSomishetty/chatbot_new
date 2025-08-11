import React from 'react';
import { Users, Wrench, DollarSign, Plane, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Domain, DomainInfo } from '../types';
import Header from '../components/Header';

const DomainSelection: React.FC = () => {
  const navigate = useNavigate();
  const { setSelectedDomain } = useApp();

  const domains: DomainInfo[] = [
    {
      id: 'customer-support',
      name: 'Customer Support',
      icon: 'Users',
      description: 'General inquiries, account issues, and product questions',
      color: 'from-blue-500 to-blue-600'
    },
    {
      id: 'technical-support',
      name: 'Technical Support',
      icon: 'Wrench',
      description: 'Technical issues, bug reports, and troubleshooting',
      color: 'from-green-500 to-green-600'
    },
    {
      id: 'finance',
      name: 'Finance',
      icon: 'DollarSign',
      description: 'Billing, payments, refunds, and financial queries',
      color: 'from-yellow-500 to-yellow-600'
    },
    {
      id: 'travel',
      name: 'Travel',
      icon: 'Plane',
      description: 'Bookings, cancellations, and travel arrangements',
      color: 'from-purple-500 to-purple-600'
    }
  ];

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'Users': return Users;
      case 'Wrench': return Wrench;
      case 'DollarSign': return DollarSign;
      case 'Plane': return Plane;
      default: return Users;
    }
  };

  const handleDomainSelect = (domain: Domain) => {
    setSelectedDomain(domain);
    navigate(`/chat/${domain}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900 transition-colors duration-200">
      <Header showProfile />
      
      <div className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Choose Your Support Category
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Select the category that best matches your inquiry to get connected with the right specialist
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {domains.map((domain) => {
              const IconComponent = getIcon(domain.icon);
              
              return (
                <button
                  key={domain.id}
                  onClick={() => handleDomainSelect(domain.id)}
                  className="group relative bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-start space-x-6">
                    <div className={`p-4 rounded-xl bg-gradient-to-r ${domain.color} shadow-lg group-hover:shadow-xl transition-shadow duration-300`}>
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                    
                    <div className="flex-1 text-left">
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-200">
                        {domain.name}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300 mb-4 leading-relaxed">
                        {domain.description}
                      </p>
                      
                      <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-medium">
                        <span>Get Started</span>
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-indigo-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
              );
            })}
          </div>

          <div className="mt-12 text-center">
            <div className="inline-flex items-center space-x-2 bg-blue-50 dark:bg-blue-900/20 px-6 py-3 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-blue-700 dark:text-blue-300 font-medium">
                AI Support Available 24/7
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainSelection;