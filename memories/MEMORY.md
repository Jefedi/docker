Français par défaut. Notifs = lisible humain, JAMAIS JSON brut.
§
ntfy: JAMAIS restart Hermes sans confirmation explicite.
§
HA monitoring: silence ABSOLU. Vagues = Beszel intermittent.
§
User refuse réponses négatives. Debug AUTONOME: désactiver, tester soi-même, fixer, réactiver. JAMAIS demander test utilisateur.
§
Docker: bind 127.0.0.1. Compose /srv/docker/<stack>/. Jefe déploie lui-même via cmd sed one-liner.
§
HA Assist: LiteLLM GLM-5.2 + Mistral STT/TTS. STT: provider mistral voxtral-mini-latest, fr. TTS: mistral-voxtral, Marie Neutral 5a271406. Script /opt/data/scripts/mistral_voxtral_tts.sh.
§
Hermes API: port 9119, clé API_SERVER_KEY .env, model hermes-agent. PAS tool_calls→n8n AI Agent crash. JAMAIS modifier DB SQLite n8n directement.
§
Mem0: /srv/docker/mem0/server. API(8888)+pgv(8432)+dash(3101). Auth X-API-Key m0sk_98BHx1GDGAX1T6kkZXr5LcwMZh0GgohfFH_IBCqpFyE.
§
Camofox: nav stealth http://127.0.0.1:9377. Contourne DataDome+Cloudflare. PAR DÉFAUT pour recherches web/scraping.
§
Obsidian: dossier Traductions/. Traduire v4: webhook n8n.
§
OCR/Pointage: 4 wf n8n. OCR iRdoNkAhwSAbkeT7. AutoClass y2Dd(30min). ZDR 0x9qijssc(3h). Pointage IbhmQyAdZuoV2PbG. TZ Europe/Paris. Paperless tok a8a7be59. ntfy tk_ymabd6elb6221 suivi-heures. Salaire 13€ route+25% panier19€ si client.
§
Technitium DNS: x42 Docker. DoH https://dns.jefe.al/dns-query via Pangolin. Ports 5380(web+API)/8053(DoH HTTP). NextDNS forwarder HTTPS. Blocklists StevenBlack+URLhaus+AdGuard. DNSSEC on. API token in Vaultwarden. Skill technitium-dns.
§
Pangolin: api.jefe.ovh/v1 org=jorganisation. Domains: *.jefe.al=domain2,*.jefe.ovh=domain1,*.losgalactique.fr=51vbysoaydeg6cr,*.trakii.tv=domain4. Old ID ykx3vzina5zahuf obsolete.
§
Vaultwarden: vault.jefe.al hermesagent@jefe.ovh. CLI: config server d'abord. Login/create OK, read bug EncString.
§
NE JAMAIS restart Newt sans raison—casse tunnel WG. Fix: restart stack Pangolin complet sur VPS.
§
Le Havre quartiers: Sanvic (S-A-N-V-I-C, pas Sainte-Vic ni Sandvik). Bléville, Danton, Saint-Vincent = quartiers est/nord du centre. Secteur plage = "La Plage"/front de mer (pas de nom de quartier distinct). Vérifier noms de quartiers avant d'écrire.