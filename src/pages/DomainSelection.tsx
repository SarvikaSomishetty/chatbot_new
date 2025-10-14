import React, { useState, useEffect } from 'react';
import { Users, Wrench, DollarSign, Plane, ArrowRight, Heart, GraduationCap, Leaf, Cpu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Domain, DomainInfo } from '../types';
import Header from '../components/Header';

const DomainSelection: React.FC = () => {
  const navigate = useNavigate();
  const { setSelectedDomain } = useApp();
  const [domains, setDomains] = useState<DomainInfo[]>([]);
  const [loading, setLoading] = useState(true);

  // Fallback domains in case API fails
  const fallbackDomains: DomainInfo[] = [
    {
      id: 'customer-support',
      name: 'Customer Support',
      description: 'General inquiries, account issues, and product questions',
      color: 'from-blue-500 to-blue-600',
      icon: 'Users'
    },
    {
      id: 'technical-support',
      name: 'Technical Support',
      description: 'Technical issues, bug reports, and troubleshooting',
      color: 'from-green-500 to-green-600',
      icon: 'Wrench'
    },
    {
      id: 'finance',
      name: 'Finance',
      description: 'Billing, payments, refunds, and financial queries',
      color: 'from-yellow-500 to-yellow-600',
      icon: 'DollarSign'
    },
    {
      id: 'travel',
      name: 'Travel',
      description: 'Bookings, cancellations, and travel arrangements',
      color: 'from-purple-500 to-purple-600',
      icon: 'Plane'
    },
    {
      id: 'healthcare',
      name: 'Healthcare',
      description: 'Medical information and health guidance',
      color: 'from-red-500 to-red-600',
      icon: 'Heart'
    },
    {
      id: 'education',
      name: 'Education',
      description: 'Learning support and educational guidance',
      color: 'from-indigo-500 to-indigo-600',
      icon: 'GraduationCap'
    },
    {
      id: 'environment',
      name: 'Environment',
      description: 'Environmental conservation and sustainability',
      color: 'from-emerald-500 to-emerald-600',
      icon: 'Leaf'
    },
    {
      id: 'technology',
      name: 'Technology',
      description: 'Software development and technical support',
      color: 'from-gray-500 to-gray-600',
      icon: 'Cpu'
    }
  ];

  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const response = await fetch('http://localhost:8000/domains');
        if (response.ok) {
          const data = await response.json();
          const formattedDomains = data.domains.map((domain: any) => ({
            id: domain.id,
            name: domain.name,
            description: domain.description,
            color: getColorForDomain(domain.id),
            icon: getIconForDomain(domain.id)
          }));
          setDomains(formattedDomains);
        } else {
          setDomains(fallbackDomains);
        }
      } catch (error) {
        console.error('Failed to fetch domains:', error);
        setDomains(fallbackDomains);
      } finally {
        setLoading(false);
      }
    };

    fetchDomains();
  }, []);

  const getColorForDomain = (domainId: string): string => {
    const colorMap: Record<string, string> = {
      'customer-support': 'from-blue-500 to-blue-600',
      'technical-support': 'from-green-500 to-green-600',
      'finance': 'from-yellow-500 to-yellow-600',
      'travel': 'from-purple-500 to-purple-600',
      'healthcare': 'from-red-500 to-red-600',
      'education': 'from-indigo-500 to-indigo-600',
      'environment': 'from-emerald-500 to-emerald-600',
      'technology': 'from-gray-500 to-gray-600'
    };
    return colorMap[domainId] || 'from-blue-500 to-blue-600';
  };

  const getIconForDomain = (domainId: string): string => {
    const iconMap: Record<string, string> = {
      'customer-support': 'Users',
      'technical-support': 'Wrench',
      'finance': 'DollarSign',
      'travel': 'Plane',
      'healthcare': 'Heart',
      'education': 'GraduationCap',
      'environment': 'Leaf',
      'technology': 'Cpu'
    };
    return iconMap[domainId] || 'Users';
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'Users': return Users;
      case 'Wrench': return Wrench;
      case 'DollarSign': return DollarSign;
      case 'Plane': return Plane;
      case 'Heart': return Heart;
      case 'GraduationCap': return GraduationCap;
      case 'Leaf': return Leaf;
      case 'Cpu': return Cpu;
      default: return Users;
    }
  };

  const handleDomainSelect = (domainId: string) => {
    setSelectedDomain(domainId as Domain);
    navigate(`/chat/${domainId}`);
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

          {loading ? (
            <div className="grid md:grid-cols-2 gap-6">
              {[...Array(4)].map((_, index) => (
                <div key={index} className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 animate-pulse">
                  <div className="flex items-start space-x-6">
                    <div className="w-16 h-16 bg-gray-300 dark:bg-gray-600 rounded-xl"></div>
                    <div className="flex-1">
                      <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                      <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-4"></div>
                      <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6">
              {domains.map((domain) => {
                const IconComponent = getIcon(domain.icon || 'Users');
                
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
          )}

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