import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveVacationRequest,
  createVacationRequest,
  deleteVacationRequest,
  fetchVacationBalance,
  fetchVacationRequests,
  fetchVacationRequirements,
  rejectVacationRequest,
  updateVacationBalance,
  adminDeleteVacationRequest,
  type VacationRequestCreate,
  type VacationBalanceUpdate,
} from "../../../services/api/vacation";

export const useVacationRequestsQuery = (year?: number) => {
  return useQuery({
    queryKey: ["vacation", "requests", year],
    queryFn: () => fetchVacationRequests(year),
  });
};

export const useVacationBalanceQuery = (year?: number) => {
  return useQuery({
    queryKey: ["vacation", "balance", year],
    queryFn: () => fetchVacationBalance(year),
  });
};

export const useVacationRequirementsQuery = (year: number) => {
  return useQuery({
    queryKey: ["vacation", "requirements", year],
    queryFn: () => fetchVacationRequirements(year),
  });
};

export const useCreateVacationRequestMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: VacationRequestCreate) =>
      createVacationRequest(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

export const useDeleteVacationRequestMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteVacationRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

export const useApproveVacationRequestMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => approveVacationRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

export const useRejectVacationRequestMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => rejectVacationRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

export const useAdminDeleteVacationRequestMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminDeleteVacationRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

export const useUpdateVacationBalanceMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      year,
      payload,
    }: {
      userId: string;
      year: number;
      payload: VacationBalanceUpdate;
    }) => updateVacationBalance(userId, year, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vacation"] });
    },
  });
};

