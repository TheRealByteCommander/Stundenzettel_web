import { apiClient } from "./client";

export interface Announcement {
  id: string;
  title: string;
  content: string;
  image_url?: string | null;
  image_filename?: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface AnnouncementCreate {
  title: string;
  content: string;
  image_url?: string | null;
  image_filename?: string | null;
  active?: boolean;
}

export interface AnnouncementUpdate {
  title?: string;
  content?: string;
  image_url?: string | null;
  image_filename?: string | null;
  active?: boolean;
}

export interface ImageUploadResponse {
  image_url: string;
  image_filename: string;
}

export const fetchAnnouncements = async (activeOnly = false): Promise<Announcement[]> => {
  const { data } = await apiClient.get<Announcement[]>("/announcements", {
    params: { active_only: activeOnly },
  });
  return data;
};

export const createAnnouncement = async (
  payload: AnnouncementCreate
): Promise<Announcement> => {
  const { data } = await apiClient.post<Announcement>("/announcements", payload);
  return data;
};

export const updateAnnouncement = async (
  id: string,
  payload: AnnouncementUpdate
): Promise<Announcement> => {
  const { data } = await apiClient.put<Announcement>(`/announcements/${id}`, payload);
  return data;
};

export const deleteAnnouncement = async (id: string): Promise<void> => {
  await apiClient.delete(`/announcements/${id}`);
};

export const uploadAnnouncementImage = async (
  file: File
): Promise<ImageUploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<ImageUploadResponse>(
    "/announcements/upload-image",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return data;
};

