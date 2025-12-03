import { apiClient } from "./client";

export interface Holiday {
  date: string;
  name: string;
}

export interface HolidaysResponse {
  year: number;
  holidays: Holiday[]; // Array of Holiday objects with date and name
  count: number;
}

export const fetchHolidays = async (year: number): Promise<Holiday[]> => {
  const { data } = await apiClient.get<HolidaysResponse>(`/vacation/holidays/${year}`);
  return data.holidays;
};

export const checkHoliday = async (date: string): Promise<{ is_holiday: boolean; name?: string }> => {
  const { data } = await apiClient.get<{ is_holiday: boolean; name?: string }>(
    `/vacation/check-holiday/${date}`
  );
  return data;
};

