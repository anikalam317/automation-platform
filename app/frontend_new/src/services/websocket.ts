/**
 * Polling Service for Workflow Status Updates
 * 
 * Following the event-driven architecture:
 * 1. Backend processes workflow through PostgreSQL NOTIFY/LISTEN
 * 2. Frontend polls /api/workflows endpoint for status updates
 * 3. No WebSocket needed - polling provides sufficient real-time updates
 */

export interface PollingOptions {
  interval?: number; // milliseconds
  maxRetries?: number;
  onError?: (error: Error) => void;
}

class PollingService {
  private intervals: Map<string, number> = new Map();
  private retryCount: Map<string, number> = new Map();

  /**
   * Start polling for workflow status updates
   */
  startPolling(
    key: string, 
    pollFunction: () => Promise<void>, 
    options: PollingOptions = {}
  ) {
    const { 
      interval = 2000, // Default 2 seconds as per existing frontend
      maxRetries = 3,
      onError
    } = options;

    this.stopPolling(key); // Clear any existing polling
    this.retryCount.set(key, 0);

    const poll = async () => {
      try {
        await pollFunction();
        this.retryCount.set(key, 0); // Reset retry count on success
      } catch (error) {
        const currentRetries = this.retryCount.get(key) || 0;
        
        if (currentRetries < maxRetries) {
          this.retryCount.set(key, currentRetries + 1);
          console.warn(`[Polling] Retry ${currentRetries + 1}/${maxRetries} for ${key}:`, error);
        } else {
          console.error(`[Polling] Max retries reached for ${key}:`, error);
          this.stopPolling(key);
          onError?.(error as Error);
          return;
        }
      }
      
      // Schedule next poll
      const timeoutId = setTimeout(poll, interval);
      this.intervals.set(key, timeoutId);
    };

    // Start first poll
    poll();
  }

  /**
   * Stop polling for a specific key
   */
  stopPolling(key: string) {
    const timeoutId = this.intervals.get(key);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.intervals.delete(key);
      this.retryCount.delete(key);
      console.log(`[Polling] Stopped polling for ${key}`);
    }
  }

  /**
   * Stop all polling
   */
  stopAllPolling() {
    this.intervals.forEach((timeoutId, key) => {
      clearTimeout(timeoutId);
      console.log(`[Polling] Stopped polling for ${key}`);
    });
    this.intervals.clear();
    this.retryCount.clear();
  }

  /**
   * Check if polling is active for a key
   */
  isPolling(key: string): boolean {
    return this.intervals.has(key);
  }

  /**
   * Get current polling intervals
   */
  getActivePolling(): string[] {
    return Array.from(this.intervals.keys());
  }
}

// Export singleton instance
export const pollingService = new PollingService();

/**
 * Utility function for workflow-specific polling
 * This replaces WebSocket subscriptions with polling as per the architecture
 */
export function startWorkflowPolling(
  workflowId: number,
  updateCallback: (data: any) => void,
  options?: PollingOptions
) {
  const key = `workflow-${workflowId}`;
  
  pollingService.startPolling(
    key,
    async () => {
      // This will be implemented by the calling component
      // using workflowAPI.getExecutionStatus(workflowId)
      updateCallback({ workflowId });
    },
    options
  );
}

export function stopWorkflowPolling(workflowId: number) {
  pollingService.stopPolling(`workflow-${workflowId}`);
}