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

function showView(name) {
  Object.values(views).forEach((view) => view.classList.remove('active'));
  views[name].classList.add('active');
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === name));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setPhotos(files) {
  const selectedFiles = Array.from(files).slice(0, 3);
  photoStrip.innerHTML = '';
  selectedFiles.forEach((file) => {
    const image = document.createElement('img');
    image.className = 'photo-preview';
    image.alt = file.name;
    image.src = URL.createObjectURL(file);
    photoStrip.appendChild(image);
  });
  const hasFiles = selectedFiles.length > 0;
  photoCount.textContent = `${selectedFiles.length} / 3`;
  verifyButton.disabled = !hasFiles;
  uploadZone.classList.toggle('has-files', hasFiles);
  uploadTitle.textContent = hasFiles ? `${selectedFiles.length} photo${selectedFiles.length > 1 ? 's' : ''} ready` : 'Drop photos here';
  uploadHint.textContent = hasFiles ? 'Add another angle or verify now' : 'or tap to choose from your device';
}

document.querySelectorAll('[data-view]').forEach((button) => {
  button.addEventListener('click', () => showView(button.dataset.view));
});
document.querySelectorAll('[data-back]').forEach((button) => {
  button.addEventListener('click', () => showView(button.dataset.back));
});

document.getElementById('demo-button').addEventListener('click', () => showView('result'));
verifyButton.addEventListener('click', () => showView('result'));
document.getElementById('save-button').addEventListener('click', () => showView('inventory'));
photoInput.addEventListener('change', (event) => setPhotos(event.target.files));
document.querySelectorAll('.recent-item').forEach((item) => item.addEventListener('click', () => showView('result')));
document.querySelectorAll('.history-item').forEach((item) => item.addEventListener('click', () => showView('result')));

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
  document.querySelector('#result-view .result-hero .eyebrow').lastChild.textContent = ` ${copy.eyebrow}`;
  document.querySelector('#result-title').textContent = copy.greeting.replace('Amina', firstName);
  document.querySelector('#result-title + p').textContent = copy.resultIntro;
  document.querySelector('.back-button span').textContent = copy.newCheck;
  setText('.result-date', copy.checkedNow);
  document.querySelector('.medicine-summary .source-tag').textContent = copy.activeConfirmation;
  document.querySelector('.certification-card .status-card-label').textContent = copy.regulatory;
  document.querySelector('.certification-card strong').textContent = copy.verifiedInformation;
  document.querySelector('.certification-card small').textContent = copy.registryMatch;
  document.querySelector('.voice-card .source-tag').textContent = copy.spokenNow;
  document.querySelector('.voice-card strong').textContent = `“${copy.spokenText}”`;
  document.querySelector('.translation').textContent = copy.spokenText;
  setText('.medicine-summary p', copy.medicineType);
  setText('.medicine-summary strong', copy.dosage);
  setText('.voice-badge', `◉ ${copy.voice}`);
  document.querySelector('.language-row > span').firstChild.textContent = copy.languageLabel;
  document.querySelector('.care-card strong').textContent = copy.careTitle;
  document.querySelector('.care-card small').textContent = copy.careText;
  document.querySelector('.security-card h2').textContent = copy.securityTitle;
  setText('.security-card .source-tag', copy.passed);
  document.querySelector('.bottom-nav [data-view="result"] strong').textContent = copy.verify;
  document.querySelector('[data-view="inventory"] strong').textContent = copy.inventory;
  document.getElementById('save-button').firstChild.textContent = `${copy.save} `;
  setText('#result-view .button-secondary', copy.done);
  setText('.safety-footer', `! ${copy.safetyText}`);
  setText('#verify-title', copy.uploadTitle);
  setText('#verify-view .intro-text', copy.uploadText);
  setText('#verify-view .card-heading h2', copy.addPhotos);
  setText('#inventory-title', copy.inventoryTitle);
  setText('.top-nav [data-view="result"]', copy.home);
  setText('.top-nav [data-view="how"]', copy.how);
  setText('.top-nav [data-view="inventory"]', copy.dashboard);
  document.getElementById('settings-title').textContent = copy.settings;
  settingsLanguage.value = language;
  localStorage.setItem('dawa-language', language);
  document.querySelectorAll('[data-language]').forEach((item) => item.classList.toggle('selected', item.dataset.language === language));
  document.querySelectorAll('.language-chip').forEach((item) => item.classList.toggle('active', item.dataset.language === language));
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
