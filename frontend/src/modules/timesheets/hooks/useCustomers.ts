import { useQuery } from "@tanstack/react-query";
import { fetchCustomers } from "../../../services/api/customers";
import type { Customer } from "../../../services/api/customers";

export const useCustomersQuery = () => {
  return useQuery<Customer[]>({
    queryKey: ["customers"],
    queryFn: fetchCustomers,
  });
};

