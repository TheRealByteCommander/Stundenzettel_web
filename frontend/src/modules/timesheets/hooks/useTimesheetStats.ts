import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  fetchMonthlyRank,
  fetchMonthlyStats,
} from "../../../services/api/timesheets";
import type {
  MonthlyRankResponse,
  MonthlyStatsResponse,
} from "../../../services/api/types";

export const timesheetStatsKey = (month: string) => [
  "timesheets",
  "stats",
  month,
];

export const useMonthlyStatsQuery = (month: string) =>
  useQuery<MonthlyStatsResponse, AxiosError>({
    queryKey: timesheetStatsKey(month),
    queryFn: () => fetchMonthlyStats(month),
    enabled: Boolean(month),
  });

export const useMonthlyRankQuery = (month: string) =>
  useQuery<MonthlyRankResponse, AxiosError>({
    queryKey: [...timesheetStatsKey(month), "rank"],
    queryFn: () => fetchMonthlyRank(month),
    enabled: Boolean(month),
  });

