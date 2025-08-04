import React, { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import { Ticket } from '../types';

interface TicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  domain: string;
}

const TicketModal: React.FC<TicketModalProps> = ({ isOpen, onClose, domain }) => {
  const [summary, setSummary] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ticketCreated, setTicketCreated] = useState<string | null>(null);
  const { user, addTicket } = useApp();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsSubmitting(true);

    // Simulate ticket creation
    setTimeout(() => {
      const ticketId = `TK-${Date.now()}`;
      const ticket: Ticket = {
        id: ticketId,
        userId: user.id,
        domain,
        summary,
        priority,
        status: 'open',
        createdAt: new Date(),
        slaTime: new Date(Date.now() + (priority === 'urgent' ? 2 : priority === 'high' ? 4 : 8) * 60 * 60 * 1000)
      };

      addTicket(ticket);
      setTicketCreated(ticketId);
      setSummary('');
      setPriority('medium');
      setIsSubmitting(false);
    }, 2000);
  };

  const getSLATime = (priority: string) => {
    switch (priority) {
      case 'urgent': return '2 hours';
      case 'high': return '4 hours';
      case 'medium': return '8 hours';
      case 'low': return '24 hours';
      default: return '8 hours';
    }
  };

  if (!isOpen) return null;

  if (ticketCreated) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-md w-full p-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Ticket Created Successfully
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Your ticket has been created with ID: <strong>{ticketCreated}</strong>
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mb-6">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                SLA Time: {getSLATime(priority)}
              </p>
            </div>
            <button
              onClick={() => {
                setTicketCreated(null);
                onClose();
              }}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              Continue Chatting
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            Create Support Ticket
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Domain
            </label>
            <input
              type="text"
              value={domain}
              disabled
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Issue Summary
            </label>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              required
              rows={4}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
              placeholder="Describe your issue in detail..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as any)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
            >
              <option value="low">Low (24h SLA)</option>
              <option value="medium">Medium (8h SLA)</option>
              <option value="high">High (4h SLA)</option>
              <option value="urgent">Urgent (2h SLA)</option>
            </select>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-4 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !summary.trim()}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isSubmitting ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TicketModal;