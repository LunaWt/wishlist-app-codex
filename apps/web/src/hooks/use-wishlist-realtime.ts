'use client';

import { useEffect, useRef } from 'react';

import { API_BASE } from '@/lib/api';
import { RealtimeEvent } from '@/lib/contracts';

interface UseWishlistRealtimeOptions {
  shareSlug?: string | null;
  onEvent: (event: RealtimeEvent) => void;
}

export function useWishlistRealtime({ shareSlug, onEvent }: UseWishlistRealtimeOptions) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!shareSlug) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let pingTimer: number | null = null;
    let isUnmounted = false;

    const connect = () => {
      const wsBase = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');
      socket = new WebSocket(`${wsBase.replace('/api/v1', '')}/api/v1/ws/public/w/${shareSlug}`);

      socket.onmessage = (message) => {
        try {
          const payload = JSON.parse(message.data) as RealtimeEvent;
          onEventRef.current(payload);
        } catch {
          // ignore malformed messages
        }
      };

      socket.onopen = () => {
        pingTimer = window.setInterval(() => {
          socket?.send('ping');
        }, 10_000);
      };

      socket.onclose = () => {
        if (pingTimer) window.clearInterval(pingTimer);
        if (!isUnmounted) {
          reconnectTimer = window.setTimeout(connect, 2000);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      if (pingTimer) window.clearInterval(pingTimer);
      socket?.close();
    };
  }, [shareSlug]);
}
