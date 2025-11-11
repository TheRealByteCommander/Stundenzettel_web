import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  createVehicle,
  deleteVehicle,
  fetchVehicles,
  updateVehicle,
} from "../../../services/api/vehicles";
import type {
  Vehicle,
  VehicleCreateRequest,
  VehicleUpdateRequest,
} from "../../../services/api/types";

export const vehiclesQueryKey = ["vehicles"] as const;

export const useVehiclesQuery = () =>
  useQuery<Vehicle[], AxiosError>({
    queryKey: vehiclesQueryKey,
    queryFn: fetchVehicles,
  });

export const useCreateVehicleMutation = () => {
  const client = useQueryClient();
  return useMutation<Vehicle, AxiosError, VehicleCreateRequest>({
    mutationFn: createVehicle,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: vehiclesQueryKey });
    },
  });
};

export const useUpdateVehicleMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<Vehicle, AxiosError, VehicleUpdateRequest>({
    mutationFn: (payload) => updateVehicle(id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: vehiclesQueryKey });
    },
  });
};

export const useDeleteVehicleMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: deleteVehicle,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: vehiclesQueryKey });
    },
  });
};

