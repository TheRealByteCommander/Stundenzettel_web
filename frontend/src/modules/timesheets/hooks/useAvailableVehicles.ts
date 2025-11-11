import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { fetchAvailableVehicles } from "../../../services/api/vehicles";
import type { Vehicle } from "../../../services/api/types";

export const availableVehiclesKey = ["available-vehicles"] as const;

export const useAvailableVehiclesQuery = () =>
  useQuery<Vehicle[], AxiosError>({
    queryKey: availableVehiclesKey,
    queryFn: fetchAvailableVehicles,
  });

