export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  helpful?: boolean;
}

export interface ChatQuery {
  user_id: string;
  domain: string;
  question: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  conversation_id: string;
  domain: string;
  timestamp: string;
}

export interface DomainInfo {
  id: string;
  name: string;
  description: string;
  color?: string;
  icon?: string;
}

export interface Ticket {
  id: string;
  userId: string;
  domain: string;
  summary: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in-progress' | 'resolved' | 'escalated';
  createdAt: Date;
  slaTime?: Date;
}

export type Domain = 'customer-support' | 'technical-support' | 'finance' | 'travel';

export interface DomainInfo {
  id: Domain;
  name: string;
  icon: string;
  description: string;
  color: string;
}

// Admin types
export interface Admin {
  id: string;
  username: string;
  role: string;
  created_at: string;
}

export interface AdminTicket {
  ticket_id: string;
  user_id: string;
  domain: string;
  subject: string;
  status: string;
  priority: string;
  sla_deadline: string;
  created_at: string;
  updated_at: string;
  user_name?: string;
  user_email?: string;
}

export interface AdminUser {
  _id: string;
  email: string;
  name: string;
  created_at: string;
  ticket_count: number;
}

export interface AdminStats {
  total_tickets: number;
  total_users: number;
  recent_tickets: number;
  status_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
  domain_breakdown: Record<string, number>;
}