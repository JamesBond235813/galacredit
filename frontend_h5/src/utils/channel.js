const CHANNEL_STORAGE_KEY = 'entry_channel';

export const saveEntryChannel = (channel) => {
  if (!channel?.channel_name) {
    return;
  }

  localStorage.setItem(CHANNEL_STORAGE_KEY, JSON.stringify({
    channel_name: channel.channel_name,
    sales_name: channel.sales_name || '',
    status: channel.status || 'ACTIVE'
  }));
};

export const getEntryChannel = () => {
  try {
    const raw = localStorage.getItem(CHANNEL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
};

export const clearEntryChannel = () => {
  localStorage.removeItem(CHANNEL_STORAGE_KEY);
};
