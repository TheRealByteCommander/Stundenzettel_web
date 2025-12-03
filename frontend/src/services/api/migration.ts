import { apiClient } from "./client";

export interface SourceConfig {
  type: "mongo" | "mysql";
  host?: string;
  port?: number;
  database: string;
  user?: string;
  password?: string;
  connection_string?: string;
}

export interface TargetConfig {
  mongo_url?: string;
  db_name?: string;
}

export interface MigrationRequest {
  source: SourceConfig;
  target?: TargetConfig;
  mapping_config?: Record<string, unknown>;
  skip_users?: boolean;
  skip_timesheets?: boolean;
  skip_travel_expenses?: boolean;
}

export interface MigrationStatus {
  running: boolean;
  progress: string | null;
  results: unknown | null;
  error: string | null;
}

export const testSourceConnection = async (
  source: SourceConfig
): Promise<{ success: boolean; message: string }> => {
  const { data } = await apiClient.post<{ success: boolean; message: string }>(
    "/admin/migration/test-connection",
    source
  );
  return data;
};

export const startMigration = async (
  request: MigrationRequest
): Promise<{ message: string; status: string }> => {
  const { data } = await apiClient.post<{ message: string; status: string }>(
    "/admin/migration/start",
    request
  );
  return data;
};

export const getMigrationStatus = async (): Promise<MigrationStatus> => {
  const { data } = await apiClient.get<MigrationStatus>("/admin/migration/status");
  return data;
};

