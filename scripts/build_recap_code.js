// Get OCR markdown from previous node
const ocrMarkdown = $input.first().json.ocr_markdown;

const PAPERLESS_TOKEN = '${PAPERLESS_TOKEN}';
const PAPERLESS_BASE = 'https://paperless.jefe.al/api';
const MISTRAL_KEY = '${MISTRAL_API_KEY}';

// 1. Fetch existing document types, correspondents and tags from Paperless
const [typesResp, corrResp, tagsResp] = await Promise.all([
  this.helpers.httpRequest({method:'GET', url:PAPERLESS_BASE+'/document_types/?page_size=100', headers:{Authorization:'Token '+PAPERLESS_TOKEN}, json:true}),
  this.helpers.httpRequest({method:'GET', url:PAPERLESS_BASE+'/correspondents/?page_size=100', headers:{Authorization:'Token '+PAPERLESS_TOKEN}, json:true}),
  this.helpers.httpRequest({method:'GET', url:PAPERLESS_BASE+'/tags/?page_size=100', headers:{Authorization:'Token '+PAPERLESS_TOKEN}, json:true})
]);

const typesList = typesResp.results.map(t => t.name);
const correspondentsList = corrResp.results.map(c => c.name);

// Build lookup maps (case-insensitive)
const typeMap = {};
typesResp.results.forEach(t => { typeMap[t.name.toLowerCase()] = t.id; typeMap[t.name] = t.id; });
const corrMap = {};
corrResp.results.forEach(c => { corrMap[c.name.toLowerCase()] = c.id; corrMap[c.name] = c.id; });
const tagMap = {};
tagsResp.results.forEach(t => { tagMap[t.name] = t.id; tagMap[t.name.toLowerCase()] = t.id; });

// 2. Call Mistral LLM to classify and extract
const classifyPrompt = `Tu es un assistant intelligent qui analyse et classe des documents administratifs.

On te donne le texte OCR d'un document. Tu dois:
1. Extraire TOUTES les informations visibles (dates, noms, heures, montants, etc.)
2. Déterminer le TYPE de document (parmi les types existants ci-dessous, ou en proposer un nouveau)
3. Déterminer le CORRESPONDANT (qui a émis ce document - parmi les existants ci-dessous, ou en proposer un nouveau)
4. Déterminer à QUI appartient ce document (jefe, pere, mere, autre)
5. Proposer un titre court et descriptif pour le document

Types de documents existants dans Paperless:
${JSON.stringify(typesList)}

Correspondants existants dans Paperless:
${JSON.stringify(correspondentsList)}

Règles:
- Si le type existe déjà (insensible à la casse), utilise-le. Sinon, propose un nouveau type.
- Si le correspondant existe déjà (insensible à la casse), utilise-le. Sinon, propose-en un nouveau.
- Sois intelligent face à des documents inédits. Devine le type et le correspondant logiques.
- Le titre doit être court et descriptif (ex: "Bulletin de salaire janvier 2026", "Facture EDF mars 2026")
- Pour les feuilles d'heures journalières, inclure la date dans le titre.

Réponds UNIQUEMENT en JSON:
{"type_document":"string","correspondant":"string","proprietaire":"jefe|pere|mere|autre","titre":"string","donnees_extraites":{"date":"string ou null","operateur":"string ou null","client":"string ou null","activites":["liste"],"heures":[{"label":"string","valeur":"string"}],"durees":[{"label":"string","valeur":"string"}],"lieux":["liste"],"montants":[{"label":"string","valeur":"string"}],"notes":"string ou null"}}`;

const llmPayload = {
  model: 'mistral-small-latest',
  messages: [
    {role:'system', content:classifyPrompt},
    {role:'user', content:'Voici le texte OCR à analyser:\n' + ocrMarkdown}
  ],
  temperature: 0.1,
  response_format: {type:'json_object'}
};

const llmResp = await this.helpers.httpRequest({
  method:'POST',
  url:'https://api.mistral.ai/v1/chat/completions',
  headers:{'Content-Type':'application/json','Authorization':'Bearer '+MISTRAL_KEY},
  body: JSON.stringify(llmPayload),
  json: true,
  timeout: 30000
});

const content = llmResp.choices[0].message.content;
const data = JSON.parse(content);

// 3. Find or create document type
let docTypeId = typeMap[data.type_document.toLowerCase()];
if (!docTypeId) {
  const newType = await this.helpers.httpRequest({
    method:'POST', url:PAPERLESS_BASE+'/document_types/',
    headers:{Authorization:'Token '+PAPERLESS_TOKEN,'Content-Type':'application/json'},
    body: JSON.stringify({name:data.type_document}),
    json:true
  });
  docTypeId = newType.id;
}

// 4. Find or create correspondent
let corrId = corrMap[data.correspondant.toLowerCase()];
if (!corrId) {
  const newCorr = await this.helpers.httpRequest({
    method:'POST', url:PAPERLESS_BASE+'/correspondents/',
    headers:{Authorization:'Token '+PAPERLESS_TOKEN,'Content-Type':'application/json'},
    body: JSON.stringify({name:data.correspondant}),
    json:true
  });
  corrId = newCorr.id;
}

// 5. Get ZDR tag id
const zdrTagId = tagMap['zdr/j-31'];

// 6. Build recap message
let recap = '📄 Document: ' + (data.type_document||'Non identifié') + '\n';
recap += '🏢 Émetteur: ' + (data.correspondant||'?') + '\n';
recap += '👤 Propriétaire: ' + (data.proprietaire||'?') + '\n';
recap += '📝 Titre: ' + (data.titre||'?') + '\n';
const d = data.donnees_extraites || {};
if (d.date) recap += '📅 Date: ' + d.date + '\n';
if (d.client) recap += '🏢 Client: ' + d.client + '\n';
if (d.heures && d.heures.length > 0) {
  recap += '\n⏰ Heures:\n';
  for (const h of d.heures) recap += '   ' + (h.label||'?') + ': ' + (h.valeur||'?') + '\n';
}
if (d.durees && d.durees.length > 0) {
  recap += '\n⏱️ Durées:\n';
  for (const dd of d.durees) recap += '   ' + (dd.label||'?') + ': ' + (dd.valeur||'?') + '\n';
}
if (d.activites && d.activites.length > 0) recap += '\n🔧 Activités: ' + d.activites.join(', ') + '\n';
if (d.lieux && d.lieux.length > 0) recap += '📍 Lieux: ' + d.lieux.join(', ') + '\n';
if (d.montants && d.montants.length > 0) {
  recap += '\n💰 Montants:\n';
  for (const m of d.montants) recap += '   ' + (m.label||'?') + ': ' + (m.valeur||'?') + '\n';
}
if (d.notes) recap += '\n📝 Notes: ' + d.notes + '\n';
recap += '\n⚠️ Vérifie ces données. Si quelque chose est faux, corrige.';

const binaryRef = $('Convert to Base64').item.binary;

return [{
  json: {
    recap_message: recap,
    extracted_data: data,
    ocr_markdown: ocrMarkdown,
    paperless_title: data.titre || 'Document',
    paperless_doc_type_id: docTypeId,
    paperless_correspondent_id: corrId,
    paperless_tags: JSON.stringify([zdrTagId].filter(Boolean))
  },
  binary: binaryRef
}];