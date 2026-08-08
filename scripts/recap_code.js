const staticData = this.getWorkflowStaticData('global');
const pointages = staticData.pointages || [];

const now = new Date();
const today = now.toLocaleDateString('sv-SE', { timeZone: 'Europe/Paris' });

const todayPointages = pointages.filter(p => p.date === today);

if (todayPointages.length === 0) {
  return [];
}

function timeToMinutes(timeStr) {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
}

function minutesToHours(min) {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h + 'h' + (m > 0 ? String(m).padStart(2, '0') : '');
}

const emojis = {
  'start_boite': '🏢', 'start_route': '🚗', 'arrivee_client': '🏗️',
  'start_pause': '🍽️', 'end_pause': '▶️', 'start_route_retour': '🚗',
  'arrivee_boite': '🏢', 'end_journee': '🏠'
};

let hBoite = 0, hClient = 0, hRoute = 0, hPause = 0;
let events = [];

todayPointages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

for (const p of todayPointages) {
  events.push((emojis[p.event]||'⏱️') + ' ' + p.label + ' - ' + p.time);
}

for (let i = 0; i < todayPointages.length - 1; i++) {
  const curr = todayPointages[i];
  const next = todayPointages[i + 1];
  const duration = timeToMinutes(next.time) - timeToMinutes(curr.time);
  if (duration <= 0) continue;

  switch(curr.event) {
    case 'start_boite':
    case 'arrivee_boite':
      if (next.event === 'start_route') hBoite += duration;
      break;
    case 'start_route':
    case 'start_route_retour':
      hRoute += duration;
      break;
    case 'arrivee_client':
      if (next.event === 'start_pause' || next.event === 'start_route_retour') hClient += duration;
      break;
    case 'start_pause':
      hPause += duration;
      break;
    case 'end_pause':
      if (next.event === 'start_route_retour' || next.event === 'start_route') hClient += duration;
      break;
  }
}

const totalWork = hBoite + hClient + hRoute;
const taux = 13.00;
const tauxSup = taux * 1.25;
const salaireNormal = (hBoite + hClient) / 60 * taux;
const salaireRoute = hRoute / 60 * tauxSup;
const panier = hClient > 0 ? 19 : 0;
const salaireTotal = salaireNormal + salaireRoute + panier;

let recap = '📊 RECAP JOURNEE ' + today + '\n\n';
recap += 'Heures:\n';
recap += '  Boite: ' + minutesToHours(hBoite) + '\n';
recap += '  Client: ' + minutesToHours(hClient) + '\n';
recap += '  Route: ' + minutesToHours(hRoute) + '\n';
recap += '  Pause: ' + minutesToHours(hPause) + '\n';
recap += '  Total: ' + minutesToHours(totalWork) + '\n\n';
recap += 'Salaire:\n';
recap += '  Normal: ' + salaireNormal.toFixed(2) + ' EUR\n';
recap += '  Route: ' + salaireRoute.toFixed(2) + ' EUR\n';
recap += '  Panier: ' + panier.toFixed(2) + ' EUR\n';
recap += '  Total: ' + salaireTotal.toFixed(2) + ' EUR\n\n';
recap += 'Pointages:\n';
for (const e of events) {
  recap += '  ' + e + '\n';
}

staticData.pointages = pointages.filter(p => p.date !== today);

return [{ json: { recap, today, total: salaireTotal } }];