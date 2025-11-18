import { Button } from "../../../components/ui/button";
import { Alert } from "../../../components/ui/alert";
import { usePushNotifications } from "../hooks/usePushNotifications";

export const PushNotificationButton = () => {
  const { isSupported, isSubscribed, subscribe, unsubscribe } = usePushNotifications();

  if (!isSupported) {
    return (
      <Alert>
        Push-Benachrichtigungen werden von Ihrem Browser nicht unterstützt.
      </Alert>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {isSubscribed ? (
        <>
          <span className="text-sm text-gray-600">Push-Benachrichtigungen aktiv</span>
          <Button variant="outline" size="sm" onClick={unsubscribe}>
            Deaktivieren
          </Button>
        </>
      ) : (
        <Button variant="outline" size="sm" onClick={subscribe}>
          Push-Benachrichtigungen aktivieren
        </Button>
      )}
    </div>
  );
};

