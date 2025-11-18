import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createAnnouncement,
  deleteAnnouncement,
  fetchAnnouncements,
  updateAnnouncement,
  uploadAnnouncementImage,
  type Announcement,
  type AnnouncementCreate,
  type AnnouncementUpdate,
} from "../../../services/api/announcements";

export const useAnnouncementsQuery = (activeOnly = false) => {
  return useQuery({
    queryKey: ["announcements", { activeOnly }],
    queryFn: () => fetchAnnouncements(activeOnly),
  });
};

export const useCreateAnnouncementMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AnnouncementCreate) => createAnnouncement(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["announcements"] });
    },
  });
};

export const useUpdateAnnouncementMutation = (id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AnnouncementUpdate) =>
      updateAnnouncement(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["announcements"] });
    },
  });
};

export const useDeleteAnnouncementMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAnnouncement(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["announcements"] });
    },
  });
};

export const useUploadAnnouncementImageMutation = () => {
  return useMutation({
    mutationFn: (file: File) => uploadAnnouncementImage(file),
  });
};

