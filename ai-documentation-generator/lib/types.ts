export type Role = "owner" | "admin" | "member";
export type InvitationStatus = "pending" | "accepted" | "revoked" | "expired";
export type UploadStatus = "uploaded" | "processing" | "completed" | "failed";
export type DocumentVisibility = "private" | "shared" | "public";

export type Organization = {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
};


export type OrganizationMember = {
  organization_id: string;
  user_id: string;
  role: Role;
  invited_by: string | null;
  joined_at: string | null;
  created_at: string;
};

export type OrganizationInvitation = {
  id: string;
  organization_id: string;
  email: string;
  role: Role;
  token: string;
  status: InvitationStatus;
  invited_by: string;
  accepted_by: string | null;
  accepted_at: string | null;
  expires_at: string;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type Upload = {
  id: string;
  organization_id: string;
  project_id: string | null;
  user_id: string;
  storage_path: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  status: UploadStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type Document = {
  id: string;
  organization_id: string;
  project_id: string | null;
  upload_id: string | null;
  title: string;
  slug: string;
  content_json: unknown;
  content_markdown: string;
  visibility: DocumentVisibility;
  share_token: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};


export type AiJobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled";

export type AiJob = {
  id: string;
  organization_id: string;
  upload_id: string | null;
  document_id: string | null;
  user_id: string;
  job_type: "document_generation";
  status: AiJobStatus;
  provider: string;
  queue_provider: string | null;
  queue_job_id: string | null;
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  attempts: number;
  max_attempts: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentVersion = {
  id: string;
  organization_id: string;
  document_id: string;
  version_number: number;
  title: string;
  content_markdown: string;
  content_json: unknown;
  change_summary: string | null;
  created_by: string | null;
  created_at: string;
};


export type ExportRecord = {
  id: string;
  organization_id: string;
  document_id: string;
  user_id: string | null;
  format: "markdown" | "html" | "pdf";
  status: "created" | "failed";
  file_name: string | null;
  error_message: string | null;
  created_at: string;
};


export type Profile = {
  user_id: string;
  full_name: string | null;
  avatar_url: string | null;
  job_title: string | null;
  timezone: string | null;
  onboarding_completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  organization_id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export type Notification = {
  id: string;
  organization_id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  href: string | null;
  read_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};
