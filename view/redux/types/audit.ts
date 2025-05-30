import { Organization } from './orgs';
import { User } from './user';

export type AuditAction = 'create' | 'update' | 'delete' | 'access';

export type AuditResourceType =
  | 'user'
  | 'organization'
  | 'role'
  | 'permission'
  | 'application'
  | 'deployment'
  | 'domain'
  | 'github_connector'
  | 'smtp_config';

export interface AuditLog {
  id: string;
  user_id: string;
  organization_id: string;
  action: AuditAction;
  resource_type: AuditResourceType;
  resource_id: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  metadata?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  request_id?: string;
  user?: User;
  organization?: Organization;
}

export interface AuditLogsResponse {
  status: string;
  message: string;
  data: AuditLog[];
}
