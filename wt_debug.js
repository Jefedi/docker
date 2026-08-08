var DATA = JSON.parse(atob(document.getElementById('__data').textContent));
var API = '/webhook/worktime';
var currentDate = new Date().toISOString().split('T')[0];
var entries = DATA.entries || [];
var stats = DATA.stats || {};

function getFeries(year){
var feries={};
var fixe=['01-01','05-01','05-08','07-14','08-15','11-01','11-11','12-25'];
fixe.forEach(function(d){feries[year+'-'+d]=true;});
var a=year%19,b=Math.floor(year/100),c=year%100;
var d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3);
var h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4;
var l=(32+2*e+2*i-h-k)%7;
var m=Math.floor((a+11*h+22*l)/451);
var month=Math.floor((h+l-7*m+114)/31);
var day=((h+l-7*m+114)%31)+1;
var paques=new Date(year,month-1,day);
var ascension=new Date(paques);ascension.setDate(paques.getDate()+40);
feries[ferieKey(ascension)]=true;
var pentecote=new Date(paques);pentecote.setDate(paques.getDate()+50);
feries[ferieKey(pentecote)]=true;
return feries;
}
function ferieKey(d){
var m=(d.getMonth()+1<10?'0':'')+(d.getMonth()+1);
var day=(d.getDate()<10?'0':'')+d.getDate();
return d.getFullYear()+'-'+m+'-'+day;
}
function isFerie(dateStr){
var d=new Date(dateStr);
var feries=getFeries(d.getFullYear());
return feries[ferieKey(d)]||false;
}
function fmtDate(iso){var p=iso.split('-');return p[2]+'/'+p[1]+'/'+p[0];}
function timeToDecimal(t){if(!t||t==='')return 0;var p=t.split(':');return Math.round((parseInt(p[0])+parseInt(p[1])/60)*100)/100;}
function decimalToTime(d){if(!d||d===0)return '00:00';var h=Math.floor(d);var m=Math.round((d-h)*60);if(m===60){h++;m=0;}return (h<10?'0':'')+h+':'+(m<10?'0':'')+m;}
function fmtHours(d){if(!d||d===0)return '0h';var h=Math.floor(d);var m=Math.round((d-h)*60);if(m===0)return h+'h';return h+'h'+m;}

function showView(v,btn){document.querySelectorAll('.view').forEach(function(el){el.classList.remove('active')});document.getElementById('view-'+v).classList.add('active');document.querySelectorAll('.nav button').forEach(function(b){b.classList.remove('active')});if(btn)btn.classList.add('active');if(v==='history')renderHistory();if(v==='stats')renderStats();if(v==='paye')renderPaye();}

function selectType(t){document.getElementById('f-type').value=t;document.getElementById('btn-boite').classList.toggle('active',t==='boite');document.getElementById('btn-dep').classList.toggle('active',t==='deplacement');document.getElementById('boite-fields').classList.toggle('hide',t!=='boite');document.getElementById('dep-fields').classList.toggle('show',t==='deplacement');}

function updateSummary(){var d=document.getElementById('f-debut').value,f=document.getElementById('f-fin').value;if(d&&f){var dh=parseInt(d.split(':')[0])*60+parseInt(d.split(':')[1]);var fh=parseInt(f.split(':')[0])*60+parseInt(f.split(':')[1]);var diff=(fh-dh);if(diff<0)diff+=1440;document.getElementById('total-display').textContent=fmtHours(diff/60);}else{document.getElementById('total-display').textContent='0h';}}

function changeDate(delta){var dp=document.getElementById('datePicker');var d=new Date(dp.value);d.setDate(d.getDate()+delta);dp.value=d.toISOString().split('T')[0];loadDate(dp.value);}

function loadDate(dateStr){currentDate=dateStr;document.getElementById('f-date').value=dateStr;var found=entries.find(function(e){return e.date===dateStr});document.getElementById('f-type').value=found?found.jour_type:'boite';document.getElementById('f-debut').value=found?found.heure_debut:'';document.getElementById('f-fin').value=found?found.heure_fin:'';document.getElementById('f-ticket').checked=found?found.ticket_resto:false;var isFerieDay=isFerie(dateStr);
document.getElementById('ferie-box').style.display=isFerieDay?'flex':'none';
document.getElementById('f-ferie').checked=found?found.jour_ferie:isFerieDay;document.getElementById('f-lieu').value=found?found.lieu_deplacement:'';document.getElementById('f-route').value=found?decimalToTime(found.heures_route):'02:30';document.getElementById('f-detour').value=found?decimalToTime(found.detour_heures):'00:00';document.getElementById('f-paniers').value=found?found.nb_paniers:'';document.getElementById('f-notes').value=found?found.notes:'';selectType(found?found.jour_type:'boite');updateSummary();var days=['Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'];var d=new Date(dateStr);document.getElementById('day-label').textContent=days[d.getDay()]+' '+fmtDate(dateStr);}

function saveEntry(e){e.preventDefault();var fd=new FormData(document.getElementById('workForm'));var data={};fd.forEach(function(v,k){if(k==='ticket_resto'){data[k]=true;return;}if(k==='jour_ferie'){data[k]=true;return;}if(k==='heures_route'||k==='detour_heures'){data[k]=timeToDecimal(v);return;}if(k==='nb_paniers'){data[k]=parseInt(v)||0;return;}data[k]=v;});if(!data.ticket_resto)data.ticket_resto=false;if(!data.jour_ferie)data.jour_ferie=false;if(data.heure_debut&&data.heure_fin){var dh=parseInt(data.heure_debut.split(':')[0])*60+parseInt(data.heure_debut.split(':')[1]);var fh=parseInt(data.heure_fin.split(':')[0])*60+parseInt(data.heure_fin.split(':')[1]);var diff=(fh-dh);if(diff<0)diff+=1440;data.heures_travaillees=Math.round(diff/60*100)/100;}else{data.heures_travaillees=0;}if(data.jour_type==='boite'){data.heures_route=0;data.detour_heures=0;data.nb_paniers=0;data.lieu_deplacement='';}fetch(API+'/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(function(r){return r.json()}).then(function(res){var idx=entries.findIndex(function(e){return e.date===data.date});if(idx>=0)entries[idx]=data;else entries.push(data);showAlert('✅ Journée enregistrée !');}).catch(function(err){showAlert('❌ Erreur: '+err)});return false;}

function deleteEntry(dateStr){if(!confirm('Supprimer la journée du '+fmtDate(dateStr)+' ?'))return;fetch(API+'/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({date:dateStr})}).then(function(r){return r.json()}).then(function(){entries=entries.filter(function(e){return e.date!==dateStr});renderHistory();showAlert('🗑️ Entrée supprimée');});}

function showAlert(msg){var box=document.getElementById('alert-box');box.innerHTML='<div class="alert">'+msg+'</div>';setTimeout(function(){box.innerHTML=''},3000);}

function renderHistory(){var sorted=entries.slice().sort(function(a,b){return b.date.localeCompare(a.date)});var html='';if(sorted.length===0){html='<div class="empty">Aucune entrée. Enregistre ta journée 📝</div>';}sorted.forEach(function(e){var days=['Dim','Lun','Mar','Mer','Jeu','Ven','Sam'];var d=new Date(e.date);var dayName=days[d.getDay()];var badge=e.jour_type==='boite'?'<span class="badge badge-b">🏢 Boîte</span>':'<span class="badge badge-d">🚗 Déplacement</span>';var tags='<span class="tag">⏱️ <b>'+fmtHours(e.heures_travaillees)+'</b></span>';if(e.jour_type==='deplacement'){if(e.lieu_deplacement)tags+='<span class="tag">📍 '+e.lieu_deplacement+'</span>';if(e.heures_route)tags+='<span class="tag">🛣️ <b>'+fmtHours(e.heures_route)+'</b> route</span>';if(e.detour_heures)tags+='<span class="tag">↩️ <b>'+fmtHours(e.detour_heures)+'</b> détour</span>';if(e.nb_paniers)tags+='<span class="tag">🍱 <b>'+e.nb_paniers+'</b> panier(s)</span>';}if(e.jour_ferie)tags+='<span class="tag">🎉 Jour férié</span>';if(e.ticket_resto)tags+='<span class="tag">🍽️ Ticket resto</span>';html+='<div class="entry-card"><div class="entry-header"><div class="entry-date">'+fmtDate(e.date)+' <small>'+dayName+'</small></div>'+badge+'</div><div class="entry-details">'+tags+'</div>'+(e.notes?'<div class="entry-notes">💬 '+e.notes+'</div>':'')+'<div style="margin-top:10px"><button class="btn-edit" onclick="editEntry(\''+e.date+'\')">✏️ Modifier</button><button class="btn-del" onclick="deleteEntry(\''+e.date+'\')">🗑️ Supprimer</button></div></div>';});document.getElementById('history-list').innerHTML=html;}

function editEntry(dateStr){document.getElementById('datePicker').value=dateStr;loadDate(dateStr);showView('saisie',null);}

function renderStats(){var html='';html+='<div class="card"><h2>📅 Cette semaine</h2><div class="stats-grid">'+'<div class="stat-box"><div class="stat-value a">'+fmtHours(stats.week?stats.week.total_heures:0)+'</div><div class="stat-label">Heures travaillées</div></div>'+'<div class="stat-box"><div class="stat-value a2">'+fmtHours(stats.week?stats.week.total_route:0)+'</div><div class="stat-label">Heures de route</div></div>'+'<div class="stat-box"><div class="stat-value g">'+(stats.week?stats.week.total_paniers:0)+'</div><div class="stat-label">Paniers</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.week?stats.week.total_tickets:0)+'</div><div class="stat-label">Tickets resto</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.week?stats.week.jours:0)+'</div><div class="stat-label">Jours saisis</div></div>'+'<div class="stat-box"><div class="stat-value a2">'+(stats.week?stats.week.nb_deplacements:0)+'</div><div class="stat-label">Déplacements</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.week?stats.week.nb_feries:0)+'</div><div class="stat-label">Jours fériés</div></div>'+'</div></div>';html+='<div class="card"><h2>📆 Ce mois</h2><div class="stats-grid">'+'<div class="stat-box"><div class="stat-value a">'+fmtHours(stats.month?stats.month.total_heures:0)+'</div><div class="stat-label">Heures travaillées</div></div>'+'<div class="stat-box"><div class="stat-value a2">'+fmtHours(stats.month?stats.month.total_route:0)+'</div><div class="stat-label">Heures de route</div></div>'+'<div class="stat-box"><div class="stat-value g">'+(stats.month?stats.month.total_paniers:0)+'</div><div class="stat-label">Paniers</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.month?stats.month.total_tickets:0)+'</div><div class="stat-label">Tickets resto</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.month?stats.month.jours:0)+'</div><div class="stat-label">Jours saisis</div></div>'+'<div class="stat-box"><div class="stat-value a2">'+fmtHours(stats.month?stats.month.total_detour:0)+'</div><div class="stat-label">Heures détour</div></div>'+'</div></div>';html+='<div class="card"><h2>🌍 Total cumulé</h2><div class="stats-grid">'+'<div class="stat-box"><div class="stat-value a">'+fmtHours(stats.total?stats.total.total_heures:0)+'</div><div class="stat-label">Heures travaillées</div></div>'+'<div class="stat-box"><div class="stat-value a2">'+fmtHours(stats.total?stats.total.total_route:0)+'</div><div class="stat-label">Heures de route</div></div>'+'<div class="stat-box"><div class="stat-value g">'+(stats.total?stats.total.total_paniers:0)+'</div><div class="stat-label">Paniers</div></div>'+'<div class="stat-box"><div class="stat-value">'+(stats.total?stats.total.jours:0)+'</div><div class="stat-label">Jours au total</div></div>'+'</div></div>';document.getElementById('stats-content').innerHTML=html;}

function renderPaye(){
var TAUX={normal:12.80,supp25:16.00,route:16.00,prime13:1.07,panier:8.00};
var html='';
html+='<div class="card"><h1>💰 Paye</h1><h2>Calcul automatique par semaine</h2>';
html+='<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:16px;font-size:13px;color:var(--muted)">';
html+='<b style="color:var(--text)">Taux appliqués :</b><br>';
html+='Heures normales : '+TAUX.normal+' EUR/h (jusqu'à 35h/sem)<br>';
html+='Heures supp. 25% : '+TAUX.supp25+' EUR/h (au-delà de 35h)<br>';
html+='Prime 13e mois : '+TAUX.prime13+' EUR/h<br>';
html+='Heures de route : '+TAUX.route+' EUR/h<br>';
html+='Panier repas : '+TAUX.panier+' EUR<br>';
html+='Ticket resto : non compté en paye</div>';

var sorted=entries.slice().sort(function(a,b){return a.date.localeCompare(b.date)});
var weeks={};
sorted.forEach(function(e){
var d=new Date(e.date);
var day=d.getDay()||7;
var monday=new Date(d);monday.setDate(d.getDate()-day+1);
var key=monday.toISOString().split('T')[0];
if(!weeks[key])weeks[key]={start:key,entries:[],total_heures:0,total_route:0,total_supp:0,total_paniers:0,nb_jours:0};
weeks[key].entries.push(e);
weeks[key].total_heures+=(parseFloat(e.heures_travaillees)||0);
weeks[key].total_route+=(parseFloat(e.heures_route)||0);
weeks[key].total_paniers+=(parseInt(e.nb_paniers)||0);
weeks[key].nb_jours++;
});

var grandTotal={normal:0,supp:0,route:0,prime13:0,panier:0,brut:0};

Object.keys(weeks).sort().forEach(function(wk){
var w=weeks[wk];
var heuresNorm=Math.min(w.total_heures,35);
var heuresSupp=Math.max(0,w.total_heures-35);
var montantNormal=heuresNorm*TAUX.normal;
var montantSupp=heuresSupp*TAUX.supp25;
var montantRoute=w.total_route*TAUX.route;
var montantPrime13=heuresNorm*TAUX.prime13;
var montantPanier=w.total_paniers*TAUX.panier;
var brutSemaine=montantNormal+montantSupp+montantRoute+montantPrime13+montantPanier;

grandTotal.normal+=montantNormal;
grandTotal.supp+=montantSupp;
grandTotal.route+=montantRoute;
grandTotal.prime13+=montantPrime13;
grandTotal.panier+=montantPanier;
grandTotal.brut+=brutSemaine;

var endDay=new Date(wk);endDay.setDate(endDay.getDate()+6);
var endKey=endDay.toISOString().split('T')[0];

html+='<div class="card" style="border-color:var(--accent)">';
html+='<h2 style="color:var(--accent)">📅 Semaine '+fmtDate(wk)+' au '+fmtDate(endKey)+'</h2>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures normales</span><span style="color:var(--text)">'+heuresNorm.toFixed(1)+'h x '+TAUX.normal+' EUR = <b style="color:var(--accent)">'+montantNormal.toFixed(2)+' EUR</b></span></div>';
if(heuresSupp>0){
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures supp. 25%</span><span style="color:var(--text)">'+heuresSupp.toFixed(1)+'h x '+TAUX.supp25+' EUR = <b style="color:var(--accent2)">'+montantSupp.toFixed(2)+' EUR</b></span></div>';
}
if(montantPrime13>0){
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Prime 13e mois</span><span style="color:var(--text)">'+heuresNorm.toFixed(1)+'h x '+TAUX.prime13+' EUR = <b>'+montantPrime13.toFixed(2)+' EUR</b></span></div>';
}
if(montantRoute>0){
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures de route</span><span style="color:var(--text)">'+w.total_route.toFixed(1)+'h x '+TAUX.route+' EUR = <b style="color:var(--accent2)">'+montantRoute.toFixed(2)+' EUR</b></span></div>';
}
if(montantPanier>0){
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Paniers repas</span><span style="color:var(--text)">'+w.total_paniers+' x '+TAUX.panier+' EUR = <b style="color:var(--green)">'+montantPanier.toFixed(2)+' EUR</b></span></div>';
}
html+='<div style="display:flex;justify-content:space-between;padding:10px 0;font-size:18px;font-weight:800"><span>Total brut semaine</span><span style="color:var(--accent)">'+brutSemaine.toFixed(2)+' EUR</span></div>';
html+='</div>';
});

html+='<div class="card" style="border:2px solid var(--accent)"><h2>🌍 Total cumulé</h2>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures normales</span><b style="color:var(--accent)">'+grandTotal.normal.toFixed(2)+' EUR</b></div>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures supp. 25%</span><b style="color:var(--accent2)">'+grandTotal.supp.toFixed(2)+' EUR</b></div>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Prime 13e mois</span><b>'+grandTotal.prime13.toFixed(2)+' EUR</b></div>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Heures de route</span><b style="color:var(--accent2)">'+grandTotal.route.toFixed(2)+' EUR</b></div>';
html+='<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span>Paniers repas</span><b style="color:var(--green)">'+grandTotal.panier.toFixed(2)+' EUR</b></div>';
html+='<div style="display:flex;justify-content:space-between;padding:14px 0;font-size:22px;font-weight:800"><span>TOTAL BRUT</span><span style="color:var(--accent)">'+grandTotal.brut.toFixed(2)+' EUR</span></div>';
html+='</div></div>';

document.getElementById('paye-content').innerHTML=html;
}

document.getElementById('datePicker').value=currentDate;
loadDate(currentDate);