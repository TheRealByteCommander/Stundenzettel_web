import { useQuery } from "@tanstack/react-query";
import { fetchHolidays, checkHoliday } from "../../../services/api/holidays";

export const useHolidaysQuery = (year: number) => {
  return useQuery({
    queryKey: ["holidays", year],
    queryFn: () => fetchHolidays(year),
  });
};

export const useCheckHolidayQuery = (date: string) => {
  return useQuery({
    queryKey: ["holiday-check", date],
    queryFn: () => checkHoliday(date),
    enabled: !!date,
  });
};

