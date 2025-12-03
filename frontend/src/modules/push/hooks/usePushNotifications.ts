import { useEffect, useState } from "react";
import { fetchPushPublicKey, subscribePush, unsubscribePush } from "../../../services/api/push";

export const usePushNotifications = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);

  useEffect(() => {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      setIsSupported(true);
      checkSubscription();
    }
  }, []);

  const checkSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.getSubscription();
      setSubscription(sub);
      setIsSubscribed(!!sub);
    } catch (error) {
      console.error("Fehler beim Prüfen der Subscription:", error);
    }
  };

  const subscribe = async () => {
    if (!isSupported) {
      alert("Push-Benachrichtigungen werden von Ihrem Browser nicht unterstützt.");
      return;
    }

    try {
      // Service Worker registrieren
      const registration = await navigator.serviceWorker.register("/sw.js");
      await registration.update();

      // VAPID Public Key holen
      const { publicKey } = await fetchPushPublicKey();

      // Subscription erstellen
      const keyArray = urlBase64ToUint8Array(publicKey);
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: keyArray as BufferSource,
      });

      // Subscription an Backend senden
      const subscriptionData = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(subscription.getKey("p256dh")!),
          auth: arrayBufferToBase64(subscription.getKey("auth")!),
        },
      };

      await subscribePush(subscriptionData);
      setSubscription(subscription);
      setIsSubscribed(true);
    } catch (error) {
      console.error("Fehler beim Abonnieren:", error);
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler";
      alert("Fehler beim Abonnieren von Push-Benachrichtigungen: " + errorMessage);
    }
  };

  const unsubscribe = async () => {
    if (!subscription) return;

    try {
      await subscription.unsubscribe();
      await unsubscribePush({ endpoint: subscription.endpoint });
      setSubscription(null);
      setIsSubscribed(false);
    } catch (error) {
      console.error("Fehler beim Abmelden:", error);
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler";
      alert("Fehler beim Abmelden von Push-Benachrichtigungen: " + errorMessage);
    }
  };

  return {
    isSupported,
    isSubscribed,
    subscribe,
    unsubscribe,
  };
};

// Hilfsfunktionen
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

