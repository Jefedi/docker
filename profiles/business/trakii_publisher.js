import { workflow, node, trigger, sticky, placeholder, newCredential, ifElse, switchCase, merge, splitInBatches, nextBatch, languageModel, memory, tool, outputParser, embedding, embeddings, vectorStore, retriever, documentLoader, textSplitter, fromAi, expr } from '@n8n/workflow-sdk';

// ============ LLM Model (OpenRouter - utilise credential existante) ============
const openRouterModel = languageModel({
  type: '@n8n/n8n-nodes-langchain.lmChatOpenAi',
  version: 1.3,
  config: {
    name: 'OpenRouter LLM',
    parameters: {
      model: 'openai/gpt-4o-mini',
      options: {
        baseURL: 'https://openrouter.ai/api/v1'
      }
    },
    credentials: { openAiApi: newCredential('OpenRouter account') },
    position: [540, 700]
  }
});

// ============ Structured Output Parser ============
const structuredParser = outputParser({
  type: '@n8n/n8n-nodes-langchain.outputParserStructured',
  version: 1.3,
  config: {
    name: 'Post Schema',
    parameters: {
      schemaType: 'fromJson',
      jsonSchemaExample: JSON.stringify({
        x_en: "English X post (280 chars max, no hashtags spam, max 2 emojis)",
        x_fr: "French X post (280 chars max, même angle traduit, max 2 emojis)",
        threads_en: "Threads post (500 chars max, more conversational, same angle)",
        ig_caption_en: "Instagram caption (2200 chars max, with line breaks, 3-5 hashtags)",
        image_prompt: "Visual prompt for image generation (cinematic, no text overlay)",
        category: "discovery|curation|culture",
        link_utm: "https://trakii.tv/?utm_source=x&utm_medium=social&utm_campaign=launch"
      })
    },
    position: [740, 700]
  }
});

// ============ Schedule Trigger (daily 18:00) ============
const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 18:00',
    parameters: {
      rule: {
        interval: [{ field: 'cronExpression', expression: '0 18 * * *' }]
      }
    },
    position: [240, 300]
  },
  output: [{}]
});

// ============ Code: Generate Topic ============
const generateTopic = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Generate Topic',
    parameters: {
      jsCode: `// Rotate across 3 categories with thematic variations
const categories = [
  {
    name: 'discovery',
    themes: [
      'Trakt import in 1 click',
      'Aggregated ratings from IMDb + RT + Metacritic + TMDB',
      'Upcoming calendar for next episodes',
      'Public profiles with section privacy control',
      'Native themed lists, no third-party needed',
      'Privacy-first: EU-hosted, encrypted tokens, no resale'
    ]
  },
  {
    name: 'curation',
    themes: [
      'Aftersun (2022) — hidden gem worth tracking',
      'Severance S2 — keep up with upcoming episodes',
      'Perfect Days (2023) — slow cinema diary entry',
      'Le Voyage de Chihiro — rewatch ritual',
      'Top 3 Wim Wenders films to journal',
      'Hot take: Letterboxd reviews are getting too meme-y',
      'What are you watching this weekend?'
    ]
  },
  {
    name: 'culture',
    themes: [
      'Behind-the-scenes: building a journal app solo',
      'The spreadsheet vs journal debate',
      'Why we built a calendar for TV shows',
      'Nostalgia: keeping a viewing diary feels like 2005 again',
      'Building in the EU: GDPR as a feature, not a burden'
    ]
  }
];

const idx = Math.floor(Date.now() / 86400000); // deterministic daily rotation
const cat = categories[idx % categories.length];
const theme = cat.themes[Math.floor(Math.random() * cat.themes.length)];

return [{
  json: {
    category: cat.name,
    theme: theme,
    date: new Date().toISOString().slice(0,10),
    rotation_index: idx
  }
}];`
    },
    position: [540, 300]
  },
  output: [{ category: 'discovery', theme: 'Trakt import in 1 click', date: '2026-07-19', rotation_index: 0 }]
});

// ============ AI Agent ============
const aiAgent = node({
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: 'Trakii Content Agent',
    parameters: {
      promptType: 'define',
      text: expr('You are the social media voice for Trakii.tv — a viewing journal app for film lovers (movies & series, imported from Trakt, EU-hosted, privacy-first).\\n\\nTASK: Generate platform-optimized posts for today\\'s theme.\\n\\nCategory: {{ $json.category }}\\nTheme: {{ $json.theme }}\\n\\nRULES:\\n- X_EN: max 280 chars, conversational, no corporate speak, 1-2 emojis max, NO hashtag spam (max 1-2 relevant), end with subtle CTA to trakii.tv when natural\\n- X_FR: same angle in French, casual tone (pas de vouvoiement corporate), 1-2 emojis\\n- THREADS_EN: max 500 chars, more reflective/conversational, same angle expanded, no aggressive CTA\\n- IG_CAPTION_EN: max 2200 chars, with line breaks, 3-5 targeted hashtags (#filmjournal #cinephile #trakt #letterboxd #movies)\\n- IMAGE_PROMPT: a cinematic visual prompt (no text overlay, no logos), evoking the theme mood\\n- LINK_UTM: always https://trakii.tv/?utm_source=x&utm_medium=social&utm_campaign=launch\\n\\nTONE: warm cinephile, not pitchy. Think Letterboxd user, not SaaS marketer. Genuine film love.\\n\\nNEVER repeat the exact same opening twice in a row. Vary sentence structure.'),
      hasOutputParser: true,
      options: {
        systemMessage: 'You are Trakii\\'s in-house social media writer. You speak as a genuine film lover, not a marketer. You\\'ve watched Aftersun three times. You keep a journal. You hate corporate speak.'
      }
    },
    subnodes: { model: openRouterModel, outputParser: structuredParser },
    position: [840, 300]
  },
  output: [{ x_en: 'Just rewatched Aftersun and I need to talk about it...', x_fr: 'Je viens de revoir Aftersun...', threads_en: 'Three viewings in...', ig_caption_en: '...', image_prompt: 'cinematic still, warm sunset...', category: 'curation', link_utm: 'https://trakii.tv/...' }]
});

// ============ HTTP Request: Pollinations Image ============
const generateImage = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Generate Image (Pollinations)',
    parameters: {
      method: 'GET',
      url: expr('https://image.pollinations.ai/prompt/{{ encodeURIComponent($json.image_prompt) }}?width=1024&height=1024&nologo=true&seed={{ Math.floor(Math.random() * 100000) }}'),
      responseFormat: 'file',
      options: { timeout: 60000 }
    },
    position: [1140, 300]
  },
  output: [{ data: 'binary', fileName: 'trakii-post.png', mimeType: 'image/png' }]
});

// ============ Set: Compose Telegram Message ============
const composeApproval = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Compose Approval',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'tg-text', name: 'tg_text', value: expr('🎬 *Trakii Post Preview*\\n\\n*Category:* {{ $json.category }}\\n*Theme:* {{ $json.theme }}\\n\\n--- 𝕏 (EN) ---\\n{{ $json.x_en }}\\n\\n--- 𝕏 (FR) ---\\n{{ $json.x_fr }}\\n\\n--- Threads (EN) ---\\n{{ $json.threads_en }}\\n\\n--- IG Caption ---\\n{{ $json.ig_caption_en }}\\n\\n--- Image prompt ---\\n{{ $json.image_prompt }}'), type: 'string' },
          { id: 'payload', name: 'payload', value: expr('{{ JSON.stringify({ x_en: $json.x_en, x_fr: $json.x_fr, threads_en: $json.threads_en, ig_caption_en: $json.ig_caption_en, image_prompt: $json.image_prompt, link_utm: $json.link_utm, category: $json.category }) }}'), type: 'string' }
        ]
      }
    },
    position: [1440, 300]
  },
  output: [{ tg_text: '...', payload: '...' }]
});

// ============ Telegram: Send Approval Message ============
const sendApproval = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Send Approval (Telegram)',
    parameters: {
      chatId: '7509874421',
      text: expr('{{ $json.tg_text }}'),
      additionalFields: {
        parseMode: 'Markdown',
        replyMarkup: {
          values: {
            type: 'inlineKeyboard',
            values: {
              rows: [
                {
                  row: {
                    buttons: [
                      { text: '✅ Publier', callbackData: 'trakii_approve' },
                      { text: '❌ Rejeter', callbackData: 'trakii_reject' }
                    ]
                  }
                }
              ]
            }
          }
        }
      }
    },
    credentials: { telegramApi: newCredential('Telegram account') },
    position: [1740, 300]
  },
  output: [{ message_id: 123 }]
});

// ============ Webhook: Approval Callback ============
const approvalWebhook = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Approval Callback',
    parameters: {
      httpMethod: 'POST',
      path: 'trakii-approval',
      responseMode: 'onReceived',
      responseData: 'ok'
    },
    position: [240, 800]
  },
  output: [{ body: { callback_query: { data: 'trakii_approve', message: { message_id: 123, chat: { id: 7509874421 } } } } }]
});

// ============ IF: Approved? ============
const isApproved = ifElse({
  version: 2.2,
  config: {
    name: 'Approved?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.body.callback_query.data }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'trakii_approve' }
        ],
        combinator: 'and'
      }
    },
    position: [540, 800]
  }
});

// ============ HTTP Request: Post to X via xurl webhook ============
const postToX = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'Post to X',
    parameters: {
      method: 'POST',
      url: placeholder('Hermes xurl webhook URL (e.g. https://hermes.jefe.ovh/webhook/xurl-post)'),
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{ "text": {{ JSON.stringify($json.body.callback_query.message.text || "") }}, "media_url": "" }'),
      options: { timeout: 30000 }
    },
    position: [840, 720]
  },
  output: [{ ok: true, tweet_id: '123' }]
});

// ============ Telegram: Confirmation ============
const confirmPublish = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Confirm Publish',
    parameters: {
      chatId: '7509874421',
      text: expr('✅ Publié sur X !\\nTweet: {{ $json.tweet_url || "(voir profil)" }}'),
      additionalFields: { parseMode: 'Markdown' }
    },
    credentials: { telegramApi: newCredential('Telegram account') },
    position: [1140, 720]
  },
  output: [{ ok: true }]
});

// ============ Telegram: Reject Notification ============
const rejectNotify = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Reject Notify',
    parameters: {
      chatId: '7509874421',
      text: '❌ Post rejeté. Un nouveau sera généré au prochain cycle.'
    },
    credentials: { telegramApi: newCredential('Telegram account') },
    position: [840, 900]
  },
  output: [{ ok: true }]
});

// ============ Sticky note ============
const note = sticky(
  '# Trakii Social Publisher\\n\\n**Pipeline:** Schedule (18h daily) → Generate topic (3 catégories rotatives) → AI Agent (OpenRouter) → Image (Pollinations gratuite) → Telegram approval (boutons inline) → Webhook callback → Publication X.\\n\\n**Credentials:** OpenRouter (LLM), Telegram (approval + confirmation), xurl webhook (X).\\n\\n**Brand voice:** cinéphile chaleureux, FR+EN, anti-corporate.\\n\\n**UTM:** ?utm_source=x&utm_medium=social&utm_campaign=launch',
  [scheduleTrigger, aiAgent, sendApproval, isApproved],
  { color: 4 }
);

// ============ Compose workflow ============
export default workflow('trakii-publisher', 'Trakii Social Publisher')
  .add(scheduleTrigger)
  .to(generateTopic)
  .to(aiAgent)
  .to(generateImage)
  .to(composeApproval)
  .to(sendApproval)
  .add(approvalWebhook)
  .to(isApproved
    .onTrue(postToX.to(confirmPublish))
    .onFalse(rejectNotify)
  )
  .add(note);