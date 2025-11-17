export type Role = "user" | "admin" | "accounting";

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  is_admin?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export type LoginResponse =
  | {
      access_token: string;
      user: User;
      token_type: string;
    }
  | {
      requires_2fa: true;
      temp_token: string;
    }
  | {
      requires_2fa_setup: true;
      setup_token: string;
    };

export interface OtpVerifyRequest {
  otp: string;
  temp_token: string;
}

export interface TwoFaSetupResponse {
  access_token: string;
  user: User;
}

export interface TwoFaQrResponse {
  otpauth_uri: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export type TimesheetStatus = "draft" | "sent" | "approved";

export interface TimeEntry {
  date: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  tasks: string;
  customer_project: string;
  location: string;
  absence_type?: string | null;
  travel_time_minutes: number;
  include_travel_time: boolean;
  vehicle_id?: string | null;
}

export interface WeeklyTimesheet {
  id: string;
  user_id: string;
  user_name: string;
  week_start: string;
  week_end: string;
  entries: TimeEntry[];
  week_vehicle_id?: string | null;
  status: TimesheetStatus;
  signed_pdf_path?: string | null;
  signed_pdf_verified?: boolean;
  signed_pdf_verification_notes?: string | null;
  created_at?: string;
}

export interface TimesheetListResponse {
  timesheets: WeeklyTimesheet[];
}

export interface CreateTimesheetRequest {
  week_start: string;
  week_vehicle_id?: string | null;
  entries: TimeEntry[];
}

export interface UpdateTimesheetRequest {
  week_start?: string;
  entries?: TimeEntry[];
  signed_pdf_verification_notes?: string | null;
  signed_pdf_verified?: boolean | null;
  week_vehicle_id?: string | null;
}

export interface SendTimesheetEmailRequest {
  recipients?: string[];
}

export interface MonthlyUserStat {
  user_id: string;
  user_name: string;
  total_hours: number;
}

export interface MonthlyStatsResponse {
  month: string;
  stats: MonthlyUserStat[];
}

export interface MonthlyRankResponse {
  month: string;
  rank: number | null;
  total_users: number | null;
}

export type TravelExpenseStatus = "draft" | "sent" | "approved";

export interface TravelExpense {
  id: string;
  user_id: string;
  user_name: string;
  date: string;
  description: string;
  kilometers: number;
  expenses: number;
  customer_project: string;
  status: TravelExpenseStatus;
  created_at?: string;
}

export interface TravelExpenseCreate {
  date: string;
  description: string;
  kilometers: number;
  expenses: number;
  customer_project?: string;
}

export interface TravelExpenseUpdate {
  date?: string;
  description?: string;
  kilometers?: number;
  expenses?: number;
  customer_project?: string;
}

export type TravelExpenseReportStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "rejected"
  | "submitted";

export interface TravelExpenseReceipt {
  id: string;
  filename: string;
  local_path: string;
  uploaded_at: string;
  file_size: number;
  exchange_proof_path?: string | null;
  exchange_proof_filename?: string | null;
  needs_exchange_proof?: boolean;
  currency?: string | null;
}

export interface TravelExpenseReportEntry {
  date: string;
  location: string;
  customer_project: string;
  travel_time_minutes: number;
  days_count: number;
  working_hours: number;
}

export interface TravelExpenseReport {
  id: string;
  user_id: string;
  user_name: string;
  month: string;
  entries: TravelExpenseReportEntry[];
  receipts: TravelExpenseReceipt[];
  status: TravelExpenseReportStatus;
  review_notes?: string | null;
  accounting_data?: Record<string, unknown> | null;
  document_analyses?: Array<Record<string, unknown>>;
  chat_messages?: TravelExpenseReportChatMessage[];
  created_at?: string;
  updated_at?: string;
  submitted_at?: string | null;
  approved_at?: string | null;
}

export interface TravelExpenseReportUpdate {
  entries?: TravelExpenseReportEntry[];
  review_notes?: string | null;
  status?: TravelExpenseReportStatus;
}

export interface ExpenseReportMonthOption {
  value: string;
  label: string;
}

export interface TravelExpenseReportChatMessage {
  id: string;
  sender: string;
  message: string;
  created_at: string;
  role?: string | null;
}

export interface AdminUserSummary {
  id: string;
  email: string;
  name: string;
  role: Role;
  is_admin?: boolean;
  weekly_hours?: number;
}

export interface UserCreateRequest {
  email: string;
  name: string;
  password: string;
  role: Role;
  weekly_hours?: number;
}

export interface UserUpdateRequest {
  email?: string;
  name?: string;
  role?: Role;
  weekly_hours?: number;
  password?: string;
}

export interface Vehicle {
  id: string;
  name: string;
  license_plate: string;
  is_pool: boolean;
  assigned_user_id?: string | null;
  assigned_user_name?: string | null;
  created_at?: string;
}

export interface VehicleCreateRequest {
  name: string;
  license_plate: string;
  is_pool: boolean;
  assigned_user_id?: string | null;
}

export interface VehicleUpdateRequest {
  name?: string;
  license_plate?: string;
  is_pool?: boolean;
  assigned_user_id?: string | null;
}

