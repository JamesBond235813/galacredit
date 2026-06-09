export const formatMaskedEcardValue = (value) => {
  const text = String(value || '').trim();
  if (!text || text === '--') {
    return '--';
  }

  const normalized = text.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
  if (normalized.length >= 8) {
    const head = normalized.slice(0, 4);
    const tail = normalized.slice(-4);
    return `${head}-****-****-****-${tail}`;
  }

  return text.replace(/\*{5,}/g, '****');
};

export const buildEcardDisplayItems = (loan = {}) => {
  const items = Array.isArray(loan?.ecard_items) ? loan.ecard_items : [];
  if (items.length) {
    return items.map((item, index) => ({
      key: `ecard-${item.id ?? item.index ?? index}`,
      id: item.id ?? null,
      index: Number.isInteger(item.index) ? item.index : index,
      title: `京东E卡${items.length > 1 ? index + 1 : ''}`,
      faceValue: Number(item.face_value || 0),
      accountDisplay: formatMaskedEcardValue(item.account_masked),
      passwordDisplay: formatMaskedEcardValue(item.password_masked),
      expiresAt: item.expires_at || null
    }));
  }

  if (loan?.ecard_account_masked || loan?.ecard_password_masked) {
    return [{
      key: 'ecard-legacy',
      id: null,
      index: 0,
      title: '京东E卡',
      faceValue: Number(loan?.ecard_face_value || 0),
      accountDisplay: formatMaskedEcardValue(loan?.ecard_account_masked),
      passwordDisplay: formatMaskedEcardValue(loan?.ecard_password_masked),
      expiresAt: loan?.ecard_expires_at || null
    }];
  }

  return [];
};

export const buildEcardSecretParams = (item = {}) => {
  if (item.id) {
    return { item_id: item.id };
  }
  if (Number.isInteger(item.index)) {
    return { index: item.index };
  }
  return {};
};
