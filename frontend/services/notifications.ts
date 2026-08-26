import { apiClient, smartFetch } from '@/lib/api';
import { AppNotification } from '@/types';
import { DEMO_NOTIFICATIONS } from '@/lib/demoData';

export async function getNotifications(): Promise<AppNotification[]> {
  return smartFetch<AppNotification[]>(
    () => apiClient.get('/notifications'),
    () => DEMO_NOTIFICATIONS
  );
}

export async function markNotificationAsRead(id: string): Promise<void> {
  await smartFetch(
    () => apiClient.put(`/notifications/${id}/read`),
    () => {
      const n = DEMO_NOTIFICATIONS.find((item) => item.id === id);
      if (n) n.isRead = true;
      return { success: true };
    }
  );
}
