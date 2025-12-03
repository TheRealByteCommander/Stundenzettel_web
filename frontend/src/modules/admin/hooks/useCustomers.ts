import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchAllCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  type CustomerUpdate,
} from "../../../services/api/customers";

export const useCustomersQuery = () => {
  return useQuery({
    queryKey: ["customers"],
    queryFn: fetchAllCustomers,
  });
};

export const useCreateCustomerMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
    },
  });
};

export const useUpdateCustomerMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CustomerUpdate }) =>
      updateCustomer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
    },
  });
};

export const useDeleteCustomerMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
    },
  });
};

