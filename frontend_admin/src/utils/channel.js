export const CHANNEL_INVITE_CODE_LENGTH = 16;

export const generateChannelInviteCode = (length = CHANNEL_INVITE_CODE_LENGTH) => {
  const alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789';
  while (true) {
    let output = '';
    for (let i = 0; i < length; i += 1) {
      output += alphabet[Math.floor(Math.random() * alphabet.length)];
    }
    if (/[a-z]/.test(output) && /\d/.test(output)) {
      return output;
    }
  }
};
