import { useEffect, useState } from 'react';

export interface StreamEvent {
  event: string;
  source_id?: string;
  timestamp?: string;
  data?: any;
}

export function useLiveEvents(onEvent?: (evt: StreamEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamEvent | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let retryDelay = 1000;
    let timerId: any = null;

    function connect() {
      eventSource = new EventSource('/api/stream/events');

      eventSource.onopen = () => {
        setIsConnected(true);
        retryDelay = 1000;
      };

      eventSource.onmessage = (e) => {
        try {
          const parsed: StreamEvent = JSON.parse(e.data);
          setLastEvent(parsed);
          if (onEvent) {
            onEvent(parsed);
          }
        } catch (err) {
          console.error("Error parsing SSE message:", err);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        if (eventSource) {
          eventSource.close();
        }
        // Exponential backoff up to 30s
        timerId = setTimeout(() => {
          retryDelay = Math.min(retryDelay * 2, 30000);
          connect();
        }, retryDelay);
      };
    }

    connect();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
      if (timerId) {
        clearTimeout(timerId);
      }
    };
  }, []);

  return { isConnected, lastEvent };
}
