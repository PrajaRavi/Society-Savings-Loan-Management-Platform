export interface DevUser {
  email: string;
  full_name: string;
  role_title: string;
  role_description: string;
  avatar_badge: string;
  is_superadmin: boolean;
}

export interface SocietyMembershipSummary {
  id: string;
  society_id: string;
  society_name?: string;
  member_number?: string;
  status: string;
  roles: string[];
}

export interface User {
  id: string;
  email: string;
  phone?: string;
  full_name: string;
  account_status: string;
  created_at: string;
  memberships: SocietyMembershipSummary[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthContextType {
  currentUser: User | null;
  activeDevUser: DevUser | null;
  availableDevUsers: DevUser[];
  isLoading: boolean;
  switchDevPersona: (email: string) => Promise<void>;
  logout: () => void;
}
