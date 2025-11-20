import { apiClient } from "./client";

export interface Customer {
  id: string;
  name: string;
  project_name?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  name: string;
  project_name?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  active?: boolean;
}

export interface CustomerUpdate {
  name?: string;
  project_name?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  active?: boolean;
}

// Öffentliche API (für alle User - nur aktive Kunden)
export const fetchCustomers = async (): Promise<Customer[]> => {
  const { data } = await apiClient.get<Customer[]>("/customers");
  return data;
};

// Admin API
export const fetchAllCustomers = async (): Promise<Customer[]> => {
  const { data } = await apiClient.get<Customer[]>("/admin/customers");
  return data;
};

export const createCustomer = async (payload: CustomerCreate): Promise<Customer> => {
  const { data } = await apiClient.post<Customer>("/admin/customers", payload);
  return data;
};

export const updateCustomer = async (
  id: string,
  payload: CustomerUpdate
): Promise<Customer> => {
  const { data } = await apiClient.put<Customer>(`/admin/customers/${id}`, payload);
  return data;
};

export const deleteCustomer = async (id: string): Promise<void> => {
  await apiClient.delete(`/admin/customers/${id}`);
};

