const API_BASE_URL = "http://127.0.0.1:8000";

const proposalForm = document.getElementById("proposalForm");
const loadingBox = document.getElementById("loadingBox");

if (proposalForm) {
  proposalForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      project_title: document.getElementById("project_title").value.trim(),
      industry: document.getElementById("industry").value.trim(),
      duration_months: parseInt(document.getElementById("duration_months").value),
      expected_users: parseInt(document.getElementById("expected_users").value),
      tech_stack: document.getElementById("tech_stack").value
        .split(",")
        .map(item => item.trim())
        .filter(item => item !== "")
    };

    try {
      loadingBox.classList.remove("hidden");

      const response = await fetch(`${API_BASE_URL}/generate-proposal`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to generate proposal");
      }

      localStorage.setItem("generatedProposal", JSON.stringify(data));
      window.location.href = "/frontend/result.html";
    } catch (error) {
      alert("Error: " + error.message);
      console.error("Proposal generation error:", error);
    } finally {
      loadingBox.classList.add("hidden");
    }
  });
}

if (window.location.pathname.includes("result.html")) {
  const storedData = localStorage.getItem("generatedProposal");

  if (!storedData) {
    alert("No proposal data found. Please generate a proposal first.");
    window.location.href = "/frontend/generator.html";
  } else {
    const data = JSON.parse(storedData);

    const proposalText = data.proposal || "";
    const sections = splitProposalIntoSections(proposalText);

    const executiveEl = document.getElementById("executive_summary");
    const technicalEl = document.getElementById("technical_approach");
    const timelineEl = document.getElementById("timeline");
    const riskEl = document.getElementById("risk_assessment");
    const costContainer = document.getElementById("estimated_cost");
    const downloadBtn = document.getElementById("downloadPdfBtn");

    if (executiveEl) {
      executiveEl.textContent = sections.executive_summary || "No data available";
    }

    if (technicalEl) {
      technicalEl.textContent = sections.technical_approach || "No data available";
    }

    if (timelineEl) {
      timelineEl.textContent = sections.timeline || "No data available";
    }

    if (riskEl) {
      riskEl.textContent = sections.risk_assessment || "No data available";
    }

    if (costContainer) {
      costContainer.innerHTML = "";

      const card = document.createElement("div");
      card.className = "cost-item";
      card.innerHTML = `
        <h3>Total Estimated Cost</h3>
        <p>${data.cost || "No cost estimate available"}</p>
      `;
      costContainer.appendChild(card);
    }

    if (downloadBtn) {
      downloadBtn.addEventListener("click", () => {
        window.open(`${API_BASE_URL}/download-proposal`, "_blank");
      });
    }
  }
}

function splitProposalIntoSections(text) {
  const cleanText = (text || "").trim();

  if (!cleanText) {
    return {
      executive_summary: "No data available",
      technical_approach: "No data available",
      timeline: "No data available",
      risk_assessment: "No data available"
    };
  }

  const normalized = cleanText.replace(/\r/g, "");

  let executive_summary = extractSection(
    normalized,
    ["Executive Summary", "1. Executive Summary"],
    ["Technical Approach", "2. Technical Approach", "Timeline", "3. Timeline", "Risk Assessment", "4. Risk Assessment"]
  );

  let technical_approach = extractSection(
    normalized,
    ["Technical Approach", "2. Technical Approach"],
    ["Timeline", "3. Timeline", "Risk Assessment", "4. Risk Assessment"]
  );

  let timeline = extractSection(
    normalized,
    ["Timeline", "3. Timeline"],
    ["Risk Assessment", "4. Risk Assessment"]
  );

  let risk_assessment = extractSection(
    normalized,
    ["Risk Assessment", "4. Risk Assessment"],
    []
  );

  if (!executive_summary) {
    const parts = normalized.split(/\n\s*\n/);
    executive_summary = parts[0] || "No data available";
  }

  if (!technical_approach) {
    technical_approach = "No data available";
  }

  if (!timeline) {
    timeline = "No data available";
  }

  if (!risk_assessment) {
    risk_assessment = "No data available";
  }

  return {
    executive_summary: executive_summary.trim(),
    technical_approach: technical_approach.trim(),
    timeline: timeline.trim(),
    risk_assessment: risk_assessment.trim()
  };
}

function extractSection(text, startHeaders, endHeaders) {
  let startIndex = -1;
  let foundHeader = "";

  for (const header of startHeaders) {
    const index = text.toLowerCase().indexOf(header.toLowerCase());
    if (index !== -1 && (startIndex === -1 || index < startIndex)) {
      startIndex = index;
      foundHeader = header;
    }
  }

  if (startIndex === -1) {
    return "";
  }

  let contentStart = startIndex + foundHeader.length;
  let sectionText = text.substring(contentStart);

  let nearestEnd = -1;

  for (const endHeader of endHeaders) {
    const idx = sectionText.toLowerCase().indexOf(endHeader.toLowerCase());
    if (idx !== -1 && (nearestEnd === -1 || idx < nearestEnd)) {
      nearestEnd = idx;
    }
  }

  if (nearestEnd !== -1) {
    sectionText = sectionText.substring(0, nearestEnd);
  }

  return sectionText
    .replace(/^[:\-\s]+/, "")
    .trim();
}
