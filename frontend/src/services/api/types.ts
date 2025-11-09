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
}

export interface WeeklyTimesheet {
  id: string;
  user_id: string;
  user_name: string;
  week_start: string;
  week_end: string;
  entries: TimeEntry[];
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
  entries: TimeEntry[];
}

export interface UpdateTimesheetRequest {
  week_start?: string;
  entries?: TimeEntry[];
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

