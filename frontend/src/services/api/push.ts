import { apiClient } from "./client";

export interface PushPublicKeyResponse {
  publicKey: string;
}

export interface PushSubscriptionRequest {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface PushUnsubscribeRequest {
  endpoint: string;
}

export const fetchPushPublicKey = async (): Promise<PushPublicKeyResponse> => {
  const { data } = await apiClient.get<PushPublicKeyResponse>("/push/public-key");
  return data;
};

export const subscribePush = async (
  payload: PushSubscriptionRequest
): Promise<void> => {
  await apiClient.post("/push/subscribe", payload);
};

export const unsubscribePush = async (
  payload: PushUnsubscribeRequest
): Promise<void> => {
  await apiClient.post("/push/unsubscribe", payload);
};

