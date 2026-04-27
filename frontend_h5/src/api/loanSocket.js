const LOAN_WS_RECONNECT_MS = 3000;

const buildLoanSnapshotWsUrl = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    return null;
  }
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${wsProtocol}://${window.location.host}/api/loan/ws/status?token=${encodeURIComponent(token)}`;
};

export const createLoanSnapshotSubscriber = ({ onSnapshot, onAuthFailed } = {}) => {
  let socket = null;
  let reconnectTimer = null;
  let stopped = false;

  const clearReconnectTimer = () => {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const closeSocket = () => {
    if (socket) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      socket.onerror = null;
      socket.close();
      socket = null;
    }
  };

  const scheduleReconnect = () => {
    if (stopped || reconnectTimer || !localStorage.getItem('token')) {
      return;
    }
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, LOAN_WS_RECONNECT_MS);
  };

  const connect = () => {
    const wsUrl = buildLoanSnapshotWsUrl();
    if (!wsUrl || stopped) {
      return;
    }
    closeSocket();
    const currentSocket = new WebSocket(wsUrl);
    socket = currentSocket;

    currentSocket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data || '{}');
        if (payload?.type === 'loan_snapshot' && payload?.data && typeof onSnapshot === 'function') {
          onSnapshot(payload.data);
        }
      } catch (error) {
        // 忽略非预期消息，避免影响页面主流程。
      }
    };

    currentSocket.onerror = () => {
      currentSocket.close();
    };

    currentSocket.onclose = (event) => {
      if (socket === currentSocket) {
        socket = null;
      }
      if (event?.code === 1008) {
        stopped = true;
        localStorage.removeItem('token');
        if (typeof onAuthFailed === 'function') {
          onAuthFailed();
        } else {
          window.location.replace('/login');
        }
        return;
      }
      scheduleReconnect();
    };
  };

  return {
    start() {
      stopped = false;
      connect();
    },
    stop() {
      stopped = true;
      clearReconnectTimer();
      closeSocket();
    },
  };
};
