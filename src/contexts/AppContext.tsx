import React, { createContext, useContext, useState, ReactNode } from 'react';
import { User, Domain, Ticket } from '../types';

interface AppContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  selectedDomain: Domain | null;
  setSelectedDomain: (domain: Domain | null) => void;
  tickets: Ticket[];
  addTicket: (ticket: Ticket) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(() => {
    const savedDomain = localStorage.getItem('selectedDomain');
    return savedDomain as Domain | null;
  });

  const [tickets, setTickets] = useState<Ticket[]>([]);

  const handleSetUser = (newUser: User | null) => {
    setUser(newUser);
    if (newUser) {
      localStorage.setItem('user', JSON.stringify(newUser));
    } else {
      localStorage.removeItem('user');
    }
  };

  const handleSetDomain = (domain: Domain | null) => {
    setSelectedDomain(domain);
    if (domain) {
      localStorage.setItem('selectedDomain', domain);
    } else {
      localStorage.removeItem('selectedDomain');
    }
  };

  const addTicket = (ticket: Ticket) => {
    setTickets(prev => [...prev, ticket]);
  };

  return (
    <AppContext.Provider value={{
      user,
      setUser: handleSetUser,
      selectedDomain,
      setSelectedDomain: handleSetDomain,
      tickets,
      addTicket
    }}>
      {children}
    </AppContext.Provider>
  );
};