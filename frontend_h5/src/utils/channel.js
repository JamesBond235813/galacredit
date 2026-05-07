const CHANNEL_STORAGE_KEY = 'entry_channel';
const INVITE_CODE_PATTERN = /^[a-z0-9]{16}$/;

export const isValidInviteCode = (value) => INVITE_CODE_PATTERN.test(String(value || '').trim());

export const saveEntryInviteCode = (inviteCode) => {
  const code = String(inviteCode || '').trim().toLowerCase();
  if (!isValidInviteCode(code)) {
    return;
  }
  localStorage.setItem(CHANNEL_STORAGE_KEY, JSON.stringify({ invite_code: code }));
};

export const getEntryInviteCode = () => {
  try {
    const raw = localStorage.getItem(CHANNEL_STORAGE_KEY);
    const payload = raw ? JSON.parse(raw) : null;
    const code = String(payload?.invite_code || '').trim().toLowerCase();
    return isValidInviteCode(code) ? code : '';
  } catch (error) {
    return '';
  }
};

export const clearEntryChannel = () => {
  localStorage.removeItem(CHANNEL_STORAGE_KEY);
};
