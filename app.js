const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const clearChatBtn = document.getElementById("clearChat");
const sendBtn = document.getElementById("sendBtn");
const apiKeyInput = document.getElementById("apiKeyInput");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const userTpl = document.getElementById("userMessageTemplate");
const botTpl = document.getElementById("botMessageTemplate");

const API_KEY_SESSION_KEY = "nusus_user_openai_api_key";

function detectDir(text) {
  const arabicRegex = /[\u0600-\u06FF]/;
  return arabicRegex.test(text) ? "rtl" : "ltr";
}

function normalizeTextAreaHeight() {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 160)}px`;
}

function appendUserMessage(text) {
  const node = userTpl.content.firstElementChild.cloneNode(true);
  const paragraph = node.querySelector("p");
  paragraph.textContent = text;
  paragraph.dir = detectDir(text);
  chatWindow.append(node);
  scrollToBottom();
}

function appendSystemMessage(text) {
  const message = document.createElement("article");
  message.className = "message system";
  const p = document.createElement("p");
  p.textContent = text;
  p.dir = detectDir(text);
  message.append(p);
  chatWindow.append(message);
  scrollToBottom();
}

function appendBotMessage(payload, userLanguageDir) {
  const node = botTpl.content.firstElementChild.cloneNode(true);

  const answerText = node.querySelector(".answer-text");
  answerText.textContent = payload.answer;
  answerText.dir = userLanguageDir;

  const opinionsNode = node.querySelector(".opinions");
  if (!payload.opinions?.length) {
    const empty = document.createElement("p");
    empty.textContent = "No distinct opinions detected in current results.";
    empty.dir = "ltr";
    opinionsNode.append(empty);
  } else {
    payload.opinions.forEach((item, idx) => {
      const wrap = document.createElement("section");
      wrap.className = "opinion";

      const title = document.createElement("h3");
      title.textContent = item.title || `Opinion ${idx + 1}`;

      const body = document.createElement("p");
      body.textContent = item.summary || "";
      body.dir = userLanguageDir;

      const refs = document.createElement("p");
      refs.className = "opinion-refs";
      refs.textContent = `Citations: ${(item.citation_ids || []).join(", ")}`;

      wrap.append(title, body, refs);
      opinionsNode.append(wrap);
    });
  }

  const citationList = node.querySelector(".citations ul");
  citationList.innerHTML = "";

  if (!payload.citations?.length) {
    const li = document.createElement("li");
    li.textContent = "No citations available.";
    citationList.append(li);
  } else {
    payload.citations.forEach((citation) => {
      const li = document.createElement("li");
      const details = [
        citation.book_title_ar,
        citation.author_ar,
        citation.source_ref_ar,
        citation.volume ? `ج${citation.volume}` : "",
        citation.page ? `ص${citation.page}` : "",
      ]
        .filter(Boolean)
        .join(" | ");

      const text = citation.snippet_ar ? `\n${citation.snippet_ar}` : "";
      li.textContent = `[${citation.id}] ${details}${text}`;
      li.dir = "rtl";
      citationList.append(li);
    });
  }

  if (payload.notes?.length) {
    const note = document.createElement("p");
    note.className = "backend-note";
    note.textContent = payload.notes.join(" ");
    node.append(note);
  }

  chatWindow.append(node);
  scrollToBottom();
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function saveApiKey() {
  const key = apiKeyInput.value.trim();
  if (!key) {
    sessionStorage.removeItem(API_KEY_SESSION_KEY);
    appendSystemMessage("API key removed from current browser session.");
    return;
  }
  sessionStorage.setItem(API_KEY_SESSION_KEY, key);
  apiKeyInput.value = "";
  appendSystemMessage("API key saved for this session only.");
}

function loadApiKeyState() {
  const hasKey = Boolean(sessionStorage.getItem(API_KEY_SESSION_KEY));
  if (hasKey) {
    appendSystemMessage("Session API key detected. You can ask questions now.");
  } else {
    appendSystemMessage("Add your OpenAI API key above to generate multilingual answers with your own token usage.");
  }
}

async function askBackend(question) {
  const apiKey = (sessionStorage.getItem(API_KEY_SESSION_KEY) || "").trim();
  const headers = {
    "Content-Type": "application/json",
  };

  if (apiKey) {
    headers["X-OpenAI-API-Key"] = apiKey;
  }

  const response = await fetch("/api/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ question }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || "Failed to fetch response from server.";
    throw new Error(detail);
  }

  return data;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  appendUserMessage(question);
  questionInput.value = "";
  normalizeTextAreaHeight();

  sendBtn.disabled = true;
  sendBtn.textContent = "Thinking...";

  try {
    const payload = await askBackend(question);
    appendBotMessage(payload, detectDir(question));
  } catch (error) {
    appendSystemMessage(`Error: ${error.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
  }
});

saveKeyBtn.addEventListener("click", saveApiKey);
apiKeyInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    saveApiKey();
  }
});

questionInput.addEventListener("input", normalizeTextAreaHeight);

clearChatBtn.addEventListener("click", () => {
  chatWindow.innerHTML = `
    <article class="message system">
      <p>Nusus AI can answer in the same language as your question and provide multiple viewpoints with citations from source texts.</p>
    </article>
  `;
  loadApiKeyState();
  questionInput.focus();
});

loadApiKeyState();
