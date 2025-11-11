import { apiClient } from "./client";
import type {
  Vehicle,
  VehicleCreateRequest,
  VehicleUpdateRequest,
} from "./types";

export const fetchVehicles = async (): Promise<Vehicle[]> => {
  const { data } = await apiClient.get<Vehicle[]>("/vehicles");
  return data;
};

export const createVehicle = async (
  payload: VehicleCreateRequest
): Promise<Vehicle> => {
  const { data } = await apiClient.post<Vehicle>("/vehicles", payload);
  return data;
};

export const updateVehicle = async (
  id: string,
  payload: VehicleUpdateRequest
): Promise<Vehicle> => {
  const { data } = await apiClient.put<Vehicle>(`/vehicles/${id}`, payload);
  return data;
};

export const deleteVehicle = async (id: string): Promise<void> => {
  await apiClient.delete(`/vehicles/${id}`);
};

