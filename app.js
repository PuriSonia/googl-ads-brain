function payload() {
  return {
    company: document.getElementById("company").value,
    audience: document.getElementById("audience").value,
    offer: document.getElementById("offer").value,
    goal: document.getElementById("goal").value
  };
}

function show(data) {
  document.getElementById("output").textContent = JSON.stringify(data, null, 2);
}

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  return await response.json();
}

async function checkStatus() {
  const response = await fetch("/api/status");
  show(await response.json());
}

async function generateAds() {
  show({loading: "Generating ads..."});
  show(await postJSON("/api/generate", payload()));
}

async function generateImproved() {
  show({loading: "Generating improved ads using feedback loop..."});
  show(await postJSON("/api/generate-improved", payload()));
}

async function psychology() {
  show(await postJSON("/api/psychology", payload()));
}

async function logFeedback() {
  const body = {
    audience: document.getElementById("audience").value,
    headline: document.getElementById("log_headline").value,
    description: document.getElementById("log_description").value,
    metrics: {
      clicks: Number(document.getElementById("clicks").value),
      conversions: Number(document.getElementById("conversions").value),
      impressions: Number(document.getElementById("impressions").value)
    }
  };
  show(await postJSON("/api/feedback/log", body));
}

async function analyseFeedback() {
  const response = await fetch("/api/feedback/analyse");
  show(await response.json());
}
