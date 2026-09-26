const views = {
  verify: document.getElementById('verify-view'),
  result: document.getElementById('result-view'),
  inventory: document.getElementById('inventory-view'),
  history: document.getElementById('history-view'),
  help: document.getElementById('help-view'),
  how: document.getElementById('how-view'),
  login: document.getElementById('login-view')
};
const photoInput = document.getElementById('photo-input');
const photoStrip = document.getElementById('photo-strip');
const uploadZone = document.getElementById('upload-zone');
const uploadTitle = document.getElementById('upload-title');
const uploadHint = document.getElementById('upload-hint');
const photoCount = document.getElementById('photo-count');
const verifyButton = document.getElementById('verify-button');
const verifyError = document.getElementById('verify-error');

// Backend base URL. Override by setting window.DAWA_API_BASE_URL before
// this script loads (e.g. a small inline <script> tag) if the API is not
// on localhost:8000 -- never hardcode a production URL here.
const API_BASE_URL = window.DAWA_API_BASE_URL || 'http://127.0.0.1:8000';

let selectedPhotoFiles = [];
// The full last verification API response, kept so "Save to inventory"
// can send real extracted fields rather than re-deriving them from the DOM.
let lastVerificationResult = null;

function showView(name) {
  Object.values(views).forEach((view) => view.classList.remove('active'));
  views[name].classList.add('active');
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === name));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setPhotos(files) {
  selectedPhotoFiles = Array.from(files).slice(0, 3);
  photoStrip.innerHTML = '';
  selectedPhotoFiles.forEach((file) => {
    const image = document.createElement('img');
    image.className = 'photo-preview';
    image.alt = file.name;
    image.src = URL.createObjectURL(file);
    photoStrip.appendChild(image);
  });
  const hasFiles = selectedPhotoFiles.length > 0;
  photoCount.textContent = `${selectedPhotoFiles.length} / 3`;
  verifyButton.disabled = !hasFiles;
  uploadZone.classList.toggle('has-files', hasFiles);
  uploadTitle.textContent = hasFiles ? `${selectedPhotoFiles.length} photo${selectedPhotoFiles.length > 1 ? 's' : ''} ready` : 'Drop photos here';
  uploadHint.textContent = hasFiles ? 'Add another angle or verify now' : 'or tap to choose from your device';
}

// Machine category -> a short human sublabel and icon. Matches
// verification/serializers.py CATEGORY_LABELS exactly; if the backend
// adds a category this map doesn't know, it falls back to the raw label
// rather than guessing an icon that might mislead (e.g. never defaulting
// to a checkmark).
const CATEGORY_DISPLAY = {
  verified: { icon: '✓', sublabel: 'Information verified' },
  warning: { icon: '!', sublabel: 'Potential warning signs' },
  unverifiable: { icon: '?', sublabel: 'Could not verify' },
  expiry_warning: { icon: '⏰', sublabel: 'Expiry warning' }
};

function renderVerificationResult(result) {
  lastVerificationResult = result;
  const extracted = result.extracted || {};

  const display = CATEGORY_DISPLAY[result.result_category] || { icon: '?', sublabel: result.category_label };
  document.getElementById('category-icon').textContent = display.icon;
  document.getElementById('category-label').textContent = result.category_label.toUpperCase();
  document.getElementById('category-sublabel').textContent = display.sublabel;

  const name = result.product_name || 'Unidentified product';
  const strength = result.strength ? ` ${result.strength}` : '';
  document.getElementById('medicine-name-strength').textContent = `${name}${strength}`;
  document.getElementById('medicine-manufacturer').textContent = result.manufacturer || 'Manufacturer not identified';
  document.getElementById('medicine-initial').textContent = name.charAt(0).toUpperCase() || '?';

  const evidenceList = document.getElementById('evidence-list');
  evidenceList.innerHTML = '';
  (result.evidence || []).forEach((line) => {
    const li = document.createElement('li');
    li.innerHTML = '<span class="check-icon">•</span><div><p></p></div>';
    li.querySelector('p').textContent = line;
    evidenceList.appendChild(li);
  });
  document.getElementById('evidence-count').textContent = `${(result.evidence || []).length} item${(result.evidence || []).length === 1 ? '' : 's'}`;
  document.getElementById('result-date').textContent = 'CHECKED JUST NOW';

  // Swahili explanation card: only offered when the package actually had
  // printed instructions to translate -- never invented, per ADR 0004/0006.
  const swahiliCard = document.getElementById('swahili-card');
  const swahiliText = document.getElementById('swahili-text');
  const swahiliAudio = document.getElementById('swahili-audio');
  const swahiliError = document.getElementById('swahili-error');
  const speakButton = document.getElementById('speak-button');
  swahiliError.hidden = true;
  if (extracted.printed_instructions) {
    swahiliCard.hidden = false;
    if (result.swahili_text && result.swahili_audio_url) {
      swahiliText.hidden = false;
      swahiliText.textContent = result.swahili_text;
      swahiliAudio.hidden = false;
      swahiliAudio.src = result.swahili_audio_url;
      speakButton.hidden = true;
    } else {
      swahiliText.hidden = true;
      swahiliAudio.hidden = true;
      speakButton.hidden = false;
      speakButton.disabled = false;
      speakButton.textContent = '🔊 Sikiliza kwa Kiswahili';
    }
  } else {
    swahiliCard.hidden = true;
  }

  // Only offer "Save to inventory" when the extraction actually has the
  // fields the inventory API requires -- never send partially-null data
  // and never let the button imply a save that would fail.
  const canSave = Boolean(
    extracted.product_name && extracted.manufacturer && extracted.strength &&
    extracted.batch_number && extracted.expiry_raw_text
  );
  const saveButton = document.getElementById('save-button');
  saveButton.disabled = !canSave;
  document.getElementById('save-hint').hidden = canSave;
}

async function submitVerification(files) {
  verifyError.hidden = true;
  verifyButton.disabled = true;
  verifyButton.textContent = 'Checking…';

  const formData = new FormData();
  files.forEach((file) => formData.append('images', file));

  try {
    const response = await fetch(`${API_BASE_URL}/api/verifications/`, {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message = body.error || body.detail || `Request failed with status ${response.status}`;
      throw new Error(message);
    }
    const result = await response.json();
    renderVerificationResult(result);
    showView('result');
  } catch (error) {
    verifyError.hidden = false;
    verifyError.textContent = `Could not reach Dawa Verify: ${error.message}`;
  } finally {
    verifyButton.disabled = selectedPhotoFiles.length === 0;
    verifyButton.innerHTML = '<span aria-hidden="true">✦</span> Verify medicine';
  }
}

async function saveResultToInventory() {
  if (!lastVerificationResult || !lastVerificationResult.extracted) return;
  const extracted = lastVerificationResult.extracted;
  const payload = {
    verification_id: lastVerificationResult.id,
    product_name: extracted.product_name,
    manufacturer: extracted.manufacturer,
    strength: extracted.strength,
    dosage_form: extracted.dosage_form || '',
    batch_number: extracted.batch_number,
    expiry_raw_text: extracted.expiry_raw_text,
    quantity: 1,
    location: ''
  };
  try {
    const response = await fetch(`${API_BASE_URL}/api/inventory/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(JSON.stringify(body));
    }
    showView('inventory');
    loadInventory();
  } catch (error) {
    verifyError.hidden = false;
    verifyError.textContent = `Could not save to inventory: ${error.message}`;
  }
}

function statusPill(status) {
  if (status === 'expired') return '<span class="status-pill status-danger">Expired</span>';
  if (status === 'within_60_days') return '<span class="status-pill status-danger">Within 60 days</span>';
  return '<span class="status-pill status-good">Good</span>';
}

async function loadInventory() {
  const tbody = document.getElementById('inventory-table-body');
  tbody.innerHTML = '<tr><td colspan="5">Loading…</td></tr>';
  try {
    const response = await fetch(`${API_BASE_URL}/api/inventory/`);
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    const items = await response.json();

    document.getElementById('inventory-count').textContent = items.length;
    document.getElementById('inventory-expiring-count').textContent = items.filter((i) => i.status === 'within_60_days').length;
    document.getElementById('inventory-updated').textContent = items.length ? 'Just now' : '—';

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5">No stock recorded yet. Use "Add stock" to record a batch.</td></tr>';
      return;
    }
    tbody.innerHTML = items.map((item) => `
      <tr>
        <td><strong>${item.medicine}</strong><small>${item.manufacturer}</small></td>
        <td>${item.batch_number}</td>
        <td>${item.expiry_raw_text}</td>
        <td>${item.quantity}</td>
        <td>${statusPill(item.status)}</td>
      </tr>
    `).join('');
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="5">Could not load inventory: ${error.message}</td></tr>`;
  }
}

document.querySelectorAll('[data-view]').forEach((button) => {
  button.addEventListener('click', () => {
    showView(button.dataset.view);
    if (button.dataset.view === 'inventory') loadInventory();
  });
});
document.querySelectorAll('[data-back]').forEach((button) => {
  button.addEventListener('click', () => showView(button.dataset.back));
});

verifyButton.addEventListener('click', () => {
  if (selectedPhotoFiles.length === 0) return;
  submitVerification(selectedPhotoFiles);
});
document.getElementById('save-button').addEventListener('click', saveResultToInventory);
document.getElementById('speak-button').addEventListener('click', async () => {
  if (!lastVerificationResult) return;
  const speakButton = document.getElementById('speak-button');
  const swahiliError = document.getElementById('swahili-error');
  speakButton.disabled = true;
  speakButton.textContent = 'Inatafsiri…';
  swahiliError.hidden = true;
  try {
    const response = await fetch(`${API_BASE_URL}/api/verifications/${lastVerificationResult.id}/speak/`, {
      method: 'POST'
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || body.detail || `Request failed with status ${response.status}`);
    renderVerificationResult(body);
  } catch (error) {
    swahiliError.hidden = false;
    swahiliError.textContent = `Could not generate audio: ${error.message}`;
    speakButton.disabled = false;
    speakButton.textContent = '🔊 Sikiliza kwa Kiswahili';
  }
});
photoInput.addEventListener('change', (event) => setPhotos(event.target.files));

// The "Recent checks" and "History" sections still show illustrative
// static entries -- there is no backend endpoint yet to fetch a specific
// past VerificationRequest by id, so these are intentionally inert rather
// than navigating to a result view with no real data behind it.

// --- Add stock (manual pharmacy entry, proposal section 7) ---
const addStockForm = document.getElementById('add-stock-form');
const addStockError = document.getElementById('add-stock-error');
document.getElementById('add-stock-button').addEventListener('click', () => {
  addStockForm.hidden = false;
  addStockError.hidden = true;
});
document.getElementById('add-stock-cancel').addEventListener('click', () => {
  addStockForm.hidden = true;
  addStockForm.reset();
});
addStockForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  addStockError.hidden = true;
  const formData = new FormData(addStockForm);
  const payload = Object.fromEntries(formData.entries());
  payload.quantity = Number(payload.quantity);

  try {
    const response = await fetch(`${API_BASE_URL}/api/inventory/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(Object.entries(body).map(([field, msgs]) => `${field}: ${msgs}`).join(' '));
    }
    addStockForm.hidden = true;
    addStockForm.reset();
    loadInventory();
  } catch (error) {
    addStockError.hidden = false;
    addStockError.textContent = error.message || 'Could not save this batch.';
  }
});

const languageButton = document.getElementById('language-button');
const languageMenu = document.getElementById('language-menu');
const settingsBackdrop = document.getElementById('settings-backdrop');
const settingsLanguage = document.getElementById('settings-language');
const displayName = document.getElementById('display-name');
const profilePhotoInput = document.getElementById('profile-photo-input');
const translations = {
  en: {
    eyebrow: 'Your medicine assistant',
    greeting: 'Hello, Amina.',
    resultIntro: 'Here is what we found on your package.',
    newCheck: 'New check',
    activeConfirmation: 'ACTIVE CONFIRMATION',
    spokenNow: 'SPOKEN NOW',
    careTitle: 'ESSENTIAL CARE ADVICE',
    securityTitle: 'Security signals',
    regulatory: 'REGULATORY CERTIFIED',
    verifiedInformation: 'Verified information',
    registryMatch: 'National Pharmacy Board Registry match',
    languageLabel: 'Audio language',
    spokenText: 'Take 1 capsule in the morning with a full breakfast.',
    careText: 'Take with food and water. Complete all 5 prescribed days even if fever or pain subsides.',
    checkedNow: 'CHECKED JUST NOW',
    done: 'Done',
    safetyText: 'This information does not prove authenticity or replace advice from a pharmacist.',
    medicineType: 'Antibiotic · Medicine for bacteria',
    dosage: '1 capsule · 3 times daily',
    voice: 'Voice',
    passed: '3 of 3 passed',
    uploadTitle: 'Know what you are holding.',
    uploadText: 'Take a photo of the medicine package. We will read the label and show you what we can verify, in plain language.',
    addPhotos: 'Add package photos',
    inventoryTitle: 'Your inventory.',
    home: 'Home',
    how: 'How it works',
    dashboard: 'Dashboard',
    verify: 'Verify',
    inventory: 'Inventory',
    save: 'Save to inventory',
    settings: 'Account settings'
  },
  sw: {
    eyebrow: 'Msaidizi wako wa dawa',
    greeting: 'Habari, Amina.',
    resultIntro: 'Haya ndiyo tuliyopata kwenye kifurushi chako.',
    newCheck: 'Kagua nyingine',
    activeConfirmation: 'TAARIFA ILIYOTHIBITISHWA',
    spokenNow: 'INASOMWA SASA',
    careTitle: 'USHAURI MUHIMU WA AFYA',
    securityTitle: 'Alama za usalama',
    regulatory: 'IMETHIBITISHWA KISHERIA',
    verifiedInformation: 'Taarifa imethibitishwa',
    registryMatch: 'Imefanana na sajili ya Bodi ya Kitaifa ya Famasi',
    languageLabel: 'Lugha ya sauti',
    spokenText: 'Kunywa kidonge 1 asubuhi pamoja na kifungua kinywa kamili.',
    careText: 'Kunywa pamoja na chakula na maji. Maliza siku zote 5 ulizoelekezwa hata homa au maumivu yakipungua.',
    checkedNow: 'IMEKAGULIWA SASA',
    done: 'Imekamilika',
    safetyText: 'Taarifa hii haithibitishi uhalisi wa dawa wala kuchukua nafasi ya ushauri wa mfamasia.',
    medicineType: 'Antibiotiki · Dawa ya bakteria',
    dosage: 'Kidonge 1 · mara 3 kwa siku',
    voice: 'Sauti',
    passed: '3 kati ya 3 zimepita',
    uploadTitle: 'Jua unachoshikilia.',
    uploadText: 'Piga picha ya kifurushi cha dawa. Tutasoma lebo na kukuonyesha tunachoweza kuthibitisha kwa lugha rahisi.',
    addPhotos: 'Ongeza picha za kifurushi',
    inventoryTitle: 'Stoo yako.',
    home: 'Nyumbani',
    how: 'Jinsi inavyofanya kazi',
    dashboard: 'Dashibodi',
    verify: 'Kagua dawa',
    inventory: 'Stoo',
    save: 'Hifadhi kwenye stoo',
    settings: 'Mipangilio ya akaunti'
  },
  fr: {
    eyebrow: 'Votre assistant medicament',
    greeting: 'Bonjour, Amina.',
    resultIntro: 'Voici ce que nous avons trouve sur votre emballage.',
    newCheck: 'Nouvelle verification',
    activeConfirmation: 'CONFIRMATION ACTIVE',
    spokenNow: 'LECTURE EN COURS',
    careTitle: 'CONSEIL DE SECURITE',
    securityTitle: 'Signaux de securite',
    regulatory: 'CERTIFICATION REGLEMENTAIRE',
    verifiedInformation: 'Informations verifiees',
    registryMatch: 'Correspondance avec le registre national de pharmacie',
    languageLabel: 'Langue audio',
    spokenText: 'Prenez 1 capsule le matin avec un petit-dejeuner complet.',
    careText: 'Prenez avec de la nourriture et de l eau. Terminez les 5 jours prescrits meme si la fievre ou la douleur cesse.',
    checkedNow: 'VERIFIE A L INSTANT',
    done: 'Termine',
    safetyText: 'Ces informations ne prouvent pas l authenticite et ne remplacent pas l avis d un pharmacien.',
    medicineType: 'Antibiotique · Medicament antibacterien',
    dosage: '1 capsule · 3 fois par jour',
    voice: 'Audio',
    passed: '3 sur 3 valides',
    uploadTitle: 'Sachez ce que vous tenez.',
    uploadText: 'Prenez une photo de l emballage. Nous lirons l etiquette et montrerons ce que nous pouvons verifier.',
    addPhotos: 'Ajouter des photos',
    inventoryTitle: 'Votre inventaire.',
    home: 'Accueil',
    how: 'Comment ca marche',
    dashboard: 'Tableau de bord',
    verify: 'Verifier',
    inventory: 'Inventaire',
    save: 'Enregistrer dans le stock',
    settings: 'Parametres du compte'
  }
};

function applyLanguage(language) {
  const copy = translations[language] || translations.en;
  const currentName = displayName.value.trim() || 'Amina Mwangi';
  const firstName = currentName.split(' ')[0];
  const setText = (selector, value) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  };
  document.documentElement.lang = language === 'sw' ? 'sw' : language;
  languageButton.firstChild.textContent = `${language.toUpperCase()} `;
  // Result-view chrome that is still static copy (not derived from a live
  // verification). Anything that used to translate the old fabricated
  // certification/voice/security claims has been removed along with that
  // markup -- see the result-view rewrite. renderVerificationResult()
  // owns the dynamic parts (category label, evidence, medicine name) and
  // is re-run after a language change below so real data isn't clobbered
  // by static copy.
  const eyebrow = document.querySelector('#result-view .result-hero .eyebrow');
  if (eyebrow && eyebrow.lastChild) eyebrow.lastChild.textContent = ` ${copy.eyebrow}`;
  setText('#result-title', copy.greeting.replace('Amina', firstName));
  setText('#result-title + p', copy.resultIntro);
  setText('.back-button span', copy.newCheck);
  setText('.result-date', copy.checkedNow);
  setText('#result-view .button-secondary', copy.done);
  setText('.safety-footer', `! ${copy.safetyText}`);
  setText('#verify-title', copy.uploadTitle);
  setText('#verify-view .intro-text', copy.uploadText);
  setText('#verify-view .card-heading h2', copy.addPhotos);
  setText('#inventory-title', copy.inventoryTitle);
  setText('.top-nav [data-view="result"]', copy.home);
  setText('.top-nav [data-view="how"]', copy.how);
  setText('.top-nav [data-view="inventory"]', copy.dashboard);
  setText('.bottom-nav [data-view="result"] strong', copy.verify);
  setText('[data-view="inventory"] strong', copy.inventory);
  const saveLabel = document.getElementById('save-button')?.firstChild;
  if (saveLabel) saveLabel.textContent = `${copy.save} `;
  const settingsTitle = document.getElementById('settings-title');
  if (settingsTitle) settingsTitle.textContent = copy.settings;
  settingsLanguage.value = language;
  localStorage.setItem('dawa-language', language);
  document.querySelectorAll('[data-language]').forEach((item) => item.classList.toggle('selected', item.dataset.language === language));
  // Re-render the last real result (if any) so dynamic content stays
  // correct after a language change instead of being left stale.
  if (lastVerificationResult) renderVerificationResult(lastVerificationResult);
}

function closeLanguageMenu() {
  languageMenu.classList.remove('open');
  languageButton.setAttribute('aria-expanded', 'false');
}

languageButton.addEventListener('click', (event) => {
  event.stopPropagation();
  const isOpen = languageMenu.classList.toggle('open');
  languageButton.setAttribute('aria-expanded', String(isOpen));
});
document.querySelectorAll('[data-language]').forEach((item) => {
  item.addEventListener('click', () => {
    applyLanguage(item.dataset.language);
    closeLanguageMenu();
  });
});
document.addEventListener('click', closeLanguageMenu);

function openSettings() {
  settingsBackdrop.hidden = false;
  displayName.focus();
}

function closeSettings() {
  settingsBackdrop.hidden = true;
}

document.querySelector('.profile-button').addEventListener('click', openSettings);
document.getElementById('close-settings').addEventListener('click', closeSettings);
settingsBackdrop.addEventListener('click', (event) => {
  if (event.target === settingsBackdrop) closeSettings();
});
profilePhotoInput.addEventListener('change', (event) => {
  const [file] = event.target.files;
  if (!file) return;
  const reader = new FileReader();
  reader.addEventListener('load', () => {
    document.querySelector('.profile-photo').src = reader.result;
    localStorage.setItem('dawa-profile-photo', reader.result);
  });
  reader.readAsDataURL(file);
});
document.getElementById('save-settings').addEventListener('click', () => {
  const name = displayName.value.trim() || 'Amina Mwangi';
  const firstName = name.split(' ')[0];
  document.getElementById('settings-name-preview').textContent = name;
  document.getElementById('result-title').textContent = `${translations[settingsLanguage.value].greeting.replace('Amina', firstName)}`;
  document.querySelector('.profile-button').textContent = name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase();
  document.querySelector('.account-avatar').textContent = document.querySelector('.profile-button').textContent;
  localStorage.setItem('dawa-name', name);
  applyLanguage(settingsLanguage.value);
  closeSettings();
});
document.getElementById('login-form').addEventListener('submit', (event) => {
  event.preventDefault();
  localStorage.setItem('dawa-signed-in', 'true');
  showView('result');
});
document.getElementById('logout-button').addEventListener('click', () => {
  localStorage.removeItem('dawa-signed-in');
  closeSettings();
  showView('login');
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeLanguageMenu();
    closeSettings();
  }
});

const savedLanguage = localStorage.getItem('dawa-language') || 'en';
const savedName = localStorage.getItem('dawa-name');
const savedProfilePhoto = localStorage.getItem('dawa-profile-photo');
if (savedName) {
  displayName.value = savedName;
  document.getElementById('settings-name-preview').textContent = savedName;
}
if (savedProfilePhoto) document.querySelector('.profile-photo').src = savedProfilePhoto;
applyLanguage(savedLanguage);

// Always start on the upload screen, regardless of which section the
// static HTML happens to mark "active" -- prevents a repeat of the bug
// where the exported markup booted straight into an empty result view.
showView('verify');
