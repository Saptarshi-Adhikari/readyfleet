import { useEffect, useState, useRef } from 'react';

export interface StreamEvent {
  id?: string;
  event: string;
  source_id?: string;
  timestamp?: string;
  data?: any;
}

export function useLiveEvents(onEvent?: (evt: StreamEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamEvent | null>(null);
  const seenEventIds = useRef<Set<string>>(new Set());

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
          const eventKey = parsed.id || `${parsed.event}-${parsed.source_id}-${parsed.timestamp}`;
          
          if (seenEventIds.current.has(eventKey)) {
            // Duplicate event - skip processing
            return;
          }
          
          seenEventIds.current.add(eventKey);
          // Keep set bounded to last 200 events
          if (seenEventIds.current.size > 200) {
            const firstKey = Array.from(seenEventIds.current)[0];
            seenEventIds.current.delete(firstKey);
          }

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
