import React from 'react';
import { ArrowRight, MessageCircle, Users, Clock, Shield, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  const steps = [
    { number: 1, title: 'Login/Register', description: 'Create your account or sign in' },
    { number: 2, title: 'Select Domain', description: 'Choose your support category' },
    { number: 3, title: 'Chat with Bot', description: 'Get instant help from our AI assistant' }
  ];

  const features = [
    { icon: MessageCircle, title: '24/7 AI Support', description: 'Get instant answers anytime' },
    { icon: Users, title: 'Human Escalation', description: 'Connect with experts when needed' },
    { icon: Clock, title: 'Fast Response', description: 'Average response time under 30 seconds' },
    { icon: Shield, title: 'Secure & Private', description: 'Your data is encrypted and protected' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900 transition-colors duration-200">
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="mb-8">
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Get Support
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent block">
                Instantly
              </span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Experience the future of customer support with our AI-powered platform. 
              Get instant answers, create tickets, and escalate to human agents seamlessly.
            </p>
          </div>

          <div className="mb-12">
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-indigo-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <span>Get Started</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {features.map((feature, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200">
                <feature.icon className="w-8 h-8 text-blue-600 mx-auto mb-4" />
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-300 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Us Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800 transition-colors duration-200">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">About SupportHub</h2>
          <p className="text-lg text-gray-600 dark:text-gray-300 leading-relaxed mb-8">
            SupportHub revolutionizes customer service by combining cutting-edge AI technology with human expertise. 
            Our platform provides instant, accurate responses while ensuring complex issues are escalated to the right specialists. 
            We believe in making support accessible, efficient, and personal.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">50K+</div>
              <div className="text-gray-600 dark:text-gray-300">Queries Resolved</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">98%</div>
              <div className="text-gray-600 dark:text-gray-300">Satisfaction Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">24/7</div>
              <div className="text-gray-600 dark:text-gray-300">Availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* How to Use Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">How It Works</h2>
          <div className="space-y-8">
            {steps.map((step, index) => (
              <div key={index} className="flex items-start space-x-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-lg">{step.number}</span>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{step.title}</h3>
                  <p className="text-gray-600 dark:text-gray-300">{step.description}</p>
                </div>
                <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;