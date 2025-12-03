import { useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import {
  useAnnouncementsQuery,
  useCreateAnnouncementMutation,
  useDeleteAnnouncementMutation,
  useUpdateAnnouncementMutation,
  useUploadAnnouncementImageMutation,
} from "../hooks/useAnnouncements";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import type { Announcement } from "../../../services/api/announcements";

export const AnnouncementsPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAdmin = user?.role === "admin";
  const { data: announcements, isLoading, error } = useAnnouncementsQuery(!isAdmin);
  const createMutation = useCreateAnnouncementMutation();
  const deleteMutation = useDeleteAnnouncementMutation();
  const uploadImageMutation = useUploadAnnouncementImageMutation();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    active: true,
    image_url: null as string | null,
    image_filename: null as string | null,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  
  const updateMutation = useUpdateAnnouncementMutation(editingId ?? "");

  const resetForm = () => {
    setFormData({
      title: "",
      content: "",
      active: true,
      image_url: null,
      image_filename: null,
    });
    setEditingId(null);
    setShowCreateForm(false);
    setMessage(null);
    setFormError(null);
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await uploadImageMutation.mutateAsync(file);
      setFormData((prev) => ({
        ...prev,
        image_url: result.image_url,
        image_filename: result.image_filename,
      }));
    } catch (err) {
      setFormError("Bild konnte nicht hochgeladen werden.");
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setFormError(null);

    if (!formData.title || !formData.content) {
      setFormError("Bitte füllen Sie alle Pflichtfelder aus.");
      return;
    }

    try {
      if (editingId) {
        await updateMutation.mutateAsync(formData);
        setMessage("Ankündigung wurde aktualisiert.");
      } else {
        await createMutation.mutateAsync(formData);
        setMessage("Ankündigung wurde erstellt.");
      }
      resetForm();
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail ?? "Fehler beim Speichern der Ankündigung."
      );
    }
  };

  const startEdit = (announcement: Announcement) => {
    setEditingId(announcement.id);
    setFormData({
      title: announcement.title,
      content: announcement.content,
      active: announcement.active,
      image_url: announcement.image_url ?? null,
      image_filename: announcement.image_filename ?? null,
    });
    setShowCreateForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Ankündigung wirklich löschen?")) return;
    try {
      await deleteMutation.mutateAsync(id);
      setMessage("Ankündigung wurde gelöscht.");
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Fehler beim Löschen.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Ankündigungen…
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Alert variant="destructive">
          Ankündigungen konnten nicht geladen werden:{" "}
          {error instanceof Error
            ? error.message
            : typeof error === "object" && error !== null && "message" in error
              ? String((error as { message: unknown }).message)
              : "Unbekannter Fehler"}
        </Alert>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Ankündigungen
          </h1>
          <p className="text-sm text-gray-600">
            {isAdmin
              ? "Verwalten Sie Ankündigungen für alle Benutzer."
              : "Aktuelle Ankündigungen und Informationen."}
          </p>
        </div>
        {isAdmin && !showCreateForm && (
          <Button onClick={() => setShowCreateForm(true)}>
            Neue Ankündigung
          </Button>
        )}
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {formError && <Alert variant="destructive">{formError}</Alert>}

      {isAdmin && showCreateForm && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              {editingId ? "Ankündigung bearbeiten" : "Neue Ankündigung"}
            </CardTitle>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="title">Titel *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, title: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="content">Inhalt (HTML) *</Label>
                <textarea
                  id="content"
                  className="min-h-[200px] w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                  value={formData.content}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, content: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="image">Bild (optional)</Label>
                <Input
                  id="image"
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  disabled={uploadImageMutation.isPending}
                />
                {formData.image_filename && (
                  <p className="text-xs text-gray-500">
                    Bild: {formData.image_filename}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="active"
                  checked={formData.active}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, active: e.target.checked }))
                  }
                  className="h-4 w-4 rounded border-gray-300"
                />
                <Label htmlFor="active">Aktiv</Label>
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {editingId ? "Aktualisieren" : "Erstellen"}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Abbrechen
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {announcements && announcements.length > 0 ? (
          announcements.map((announcement) => (
            <Card key={announcement.id}>
              <CardContent className="space-y-4 py-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold text-brand-gray">
                      {announcement.title}
                    </h2>
                    {announcement.image_url && (
                      <img
                        src={announcement.image_url}
                        alt={announcement.image_filename ?? "Ankündigung"}
                        className="mt-2 max-h-64 rounded-lg object-contain"
                      />
                    )}
                    <div
                      className="mt-2 text-sm text-gray-700"
                      dangerouslySetInnerHTML={{ __html: announcement.content }}
                    />
                    <p className="mt-2 text-xs text-gray-500">
                      {new Date(announcement.created_at).toLocaleDateString("de-DE")}
                      {announcement.active ? (
                        <span className="ml-2 text-green-600">• Aktiv</span>
                      ) : (
                        <span className="ml-2 text-gray-400">• Inaktiv</span>
                      )}
                    </p>
                  </div>
                  {isAdmin && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => startEdit(announcement)}
                      >
                        Bearbeiten
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(announcement.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Löschen
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="py-6 text-center text-gray-500">
              Keine Ankündigungen vorhanden.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

