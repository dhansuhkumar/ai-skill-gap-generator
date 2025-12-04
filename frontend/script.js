// frontend/script.js

// Auto-detect backend URL
const isLocal =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.protocol === "file:";

const BASE_URL = isLocal
  ? "http://127.0.0.1:8080"
  : "https://ai-skill-gap-generator-production.up.railway.app";

const zipBase =
  "https://raw.githubusercontent.com/dhansuhkumar/ai-skill-gap-generator/main/backend/projects/";

let skillChartInstance = null;
let loadingInterval = null;
let loadingProgress = 0;
let loadingStepIndex = 0;

const loadingSteps = [
  "🔌 Connecting to AI engine...",
  "🧠 Analyzing your skills & target role...",
  "🧭 Mapping required vs known skills...",
  "🎯 Designing your roadmap & projects..."
];

function startLoadingUI() {
  const loading = document.getElementById("loading");
  const percentEl = document.getElementById("loadingPercent");
  const barEl = document.getElementById("loadingBar");
  const stepEl = document.getElementById("loadingStep");

  loadingProgress = 0;
  loadingStepIndex = 0;

  if (percentEl) percentEl.textContent = "0%";
  if (barEl) barEl.style.width = "0%";
  if (stepEl) stepEl.textContent = loadingSteps[0];

  if (loading) loading.classList.remove("hidden");

  if (loadingInterval) clearInterval(loadingInterval);

  loadingInterval = setInterval(() => {
    // Fake progress step – moves faster early, slows later
    const increment = loadingProgress < 60 ? Math.random() * 8 + 5 : Math.random() * 5 + 2;
    loadingProgress = Math.min(loadingProgress + increment, 97); // don't reach 100 until done

    if (percentEl) percentEl.textContent = `${Math.round(loadingProgress)}%`;
    if (barEl) barEl.style.width = `${loadingProgress}%`;

    const stepSize = 100 / loadingSteps.length;
    const targetStepIndex = Math.min(
      Math.floor(loadingProgress / stepSize),
      loadingSteps.length - 1
    );

    if (targetStepIndex !== loadingStepIndex) {
      loadingStepIndex = targetStepIndex;
      if (stepEl) stepEl.textContent = loadingSteps[loadingStepIndex];
    }
  }, 600);
}

function stopLoadingUI() {
  const loading = document.getElementById("loading");
  const percentEl = document.getElementById("loadingPercent");
  const barEl = document.getElementById("loadingBar");
  const stepEl = document.getElementById("loadingStep");

  if (loadingInterval) {
    clearInterval(loadingInterval);
    loadingInterval = null;
  }

  // Snap to 100 and show final message briefly
  if (percentEl) percentEl.textContent = "100%";
  if (barEl) barEl.style.width = "100%";
  if (stepEl) stepEl.textContent = "✅ Done! Preparing your dashboard...";

  setTimeout(() => {
    if (loading) loading.classList.add("hidden");
  }, 400);
}
// Form submission handler

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recommendForm");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");

  // Remove the old global include_youtube assignment.
  // We'll read the checkbox inside the submit handler so it's always up-to-date.

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    results.classList.add("hidden");
    startLoadingUI();

    const skillsInput = document.getElementById("skills").value;
    const skills = skillsInput
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s);

    const roleInput = document.getElementById("role").value.trim();
    if (!roleInput) {
      stopLoadingUI();
      alert("Please type or select a role.");
      return;
    }
    const role = roleInput;

    // Read the checkbox *right now*
    const includeVideosCheckbox = document.getElementById("includeVideos");
    // Only add the flag if checkbox is present AND checked
    const payload = { role, skills };
    if (includeVideosCheckbox && includeVideosCheckbox.checked) {
      payload.include_youtube = true;
      // Use the exact key your backend checks for
      payload.max_video_results = parseInt(
        document.getElementById("maxVideoResults")?.value || "3",
        10
      );
    }

    // Optional: JWT login (ignore if fails) -- NOTE: your backend login route is /login
    try {
      const authRes = await fetch(`${BASE_URL}/api/login`, { // <-- changed to /login
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "dhanush",
          password: "test123",
        }),
      });

      if (authRes.ok) {
        const authData = await authRes.json();
        // you created token under key 'token' in backend, not access_token
        if (authData.token) localStorage.setItem("jwtToken", authData.token);
      }
    } catch (err) {
      console.warn("Login skipped/failed:", err);
    }

    try {
      const response = await fetch(`${BASE_URL}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("Failed to fetch recommendations");
      const data = await response.json();
      console.log("Full /recommend response:", data);

      // Save profile silently if token exists
      const token = localStorage.getItem("jwtToken");
      if (token) {
        fetch(`${BASE_URL}/api/save_profile`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            role,
            skills,
            recommendations: ["Generated by AI"],
          }),
        }).catch((e) => console.log("Save profile ignored:", e));
      }

      updateUIWithRecommendations(data, role, skills);

      stopLoadingUI();
      results.classList.remove("hidden");
    } catch (error) {
      stopLoadingUI();
      console.error("Error:", error);
      alert("Error: " + error.message);
    }
  });
});

// Render results
function updateUIWithRecommendations(data, role, userSkills) {
  const missingSkills = data.missing_skills || [];
  const recommendedProjects = data.recommended_projects || [];
  const starterProjects = data.starter_projects || [];
  const aiProjects = data.ai_projects || [];
  const requiredSkillsAI = data.required_skills_ai || [];
  const jobMatches = data.job_matches || [];

  // A) Missing skills (tags)
  const missingContainer = document.getElementById("missingSkillsList");
  if (missingContainer) {
    if (missingSkills.length === 0) {
      missingContainer.innerHTML =
        '<span class="text-emerald-300 text-xs">You are a perfect match for this role! 🎉</span>';
    } else {
      missingContainer.innerHTML = missingSkills
        .map(
          (skill) => `
        <span class="bg-rose-500/15 text-rose-200 border border-rose-500/40 px-3 py-1 rounded-full text-[11px] font-medium">
          ${skill}
        </span>
      `
        )
        .join("");
    }
  }

  // B) Core skills for the role (AI)
  const requiredBlock = document.getElementById("requiredSkillsBlock");
  const requiredContainer = document.getElementById("requiredSkillsList");
  if (requiredBlock && requiredContainer) {
    if (requiredSkillsAI.length === 0) {
      requiredBlock.classList.add("hidden");
      requiredContainer.innerHTML = "";
    } else {
      requiredBlock.classList.remove("hidden");
      requiredContainer.innerHTML = requiredSkillsAI
        .map(
          (skill) => `
        <span class="bg-cyan-500/15 text-cyan-100 border border-cyan-400/50 px-3 py-1 rounded-full text-[11px] font-medium">
          ${skill}
        </span>
      `
        )
        .join("");
    }
  }

  // C) Job Readiness & Suitable Roles
  const jobFitRoleTitle = document.getElementById("jobFitRoleTitle");
  const jobFitSummary = document.getElementById("jobFitSummary");
  const jobFitPercent = document.getElementById("jobFitPercent");
  const jobFitLevel = document.getElementById("jobFitLevel");
  const jobFitBar = document.getElementById("jobFitBar");
  const jobMatchesList = document.getElementById("jobMatchesList");

  if (
    jobFitRoleTitle &&
    jobFitSummary &&
    jobFitPercent &&
    jobFitLevel &&
    jobFitBar &&
    jobMatchesList
  ) {
    if (!jobMatches || jobMatches.length === 0) {
      jobFitRoleTitle.textContent = role || "Role not set";
      jobFitPercent.textContent = "0%";
      jobFitBar.style.width = "0%";
      jobFitLevel.textContent = "Exploring";
      jobFitLevel.className =
        "text-[11px] mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-200 border border-slate-500/80";
      jobFitSummary.innerHTML =
        `<span class="text-[11px] text-slate-300">We don’t have enough info yet. Add more skills to see your readiness.</span>`;
      jobMatchesList.innerHTML = "";
    } else {
      let primary = jobMatches.find((j) => j.is_selected_role) || jobMatches[0];

      jobFitRoleTitle.textContent = primary.role || role || "Selected role";
      jobFitPercent.textContent = `${primary.match_percent}%`;
      jobFitBar.style.width = `${primary.match_percent}%`;

      // Level badge based on percent
      let levelText = "";
      let levelClass = "";
      if (primary.match_percent >= 80) {
        levelText = "Job-Ready";
        levelClass =
          "text-[11px] mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-100 border border-emerald-400/70";
      } else if (primary.match_percent >= 50) {
        levelText = "On Track";
        levelClass =
          "text-[11px] mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-100 border border-amber-400/70";
      } else {
        levelText = "Beginner";
        levelClass =
          "text-[11px] mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-100 border border-rose-400/70";
      }
      jobFitLevel.textContent = levelText;
      jobFitLevel.className = levelClass;

      jobFitSummary.innerHTML = `
        <span class="text-[11px] text-slate-200">
          You match <span class="font-semibold">${primary.known_count}</span> of
          <span class="font-semibold">${primary.total_required}</span> core skills for this role.
          Focus on the missing skills on the left to push this closer to 100%.
        </span>
      `;

      const others = jobMatches.filter((j) => j !== primary);
      if (others.length === 0) {
        jobMatchesList.innerHTML =
          '<p class="text-[11px] text-slate-400">We only evaluated your selected role for now.</p>';
      } else {
        jobMatchesList.innerHTML = others
          .map((j) => {
            let colorClass =
              j.match_percent >= 70
                ? "text-emerald-300"
                : j.match_percent >= 40
                ? "text-amber-300"
                : "text-rose-300";
            return `
              <div class="flex items-center justify-between text-[11px] bg-slate-900/80 rounded-lg px-3 py-2 border border-slate-700/80">
                <div class="flex flex-col">
                  <span class="font-semibold text-slate-100">${j.role}</span>
                  <span class="text-[10px] text-slate-400">
                    ${j.known_count}/${j.total_required} core skills matched
                  </span>
                </div>
                <span class="font-bold ${colorClass}">
                  ${j.match_percent}%
                </span>
              </div>
            `;
          })
          .join("");
      }
    }
  }

  // D) Project Lab: AI ideas, practice projects, starter code
  const projectContainer = document.getElementById("projectContainer");
  const aiBox = document.getElementById("aiProjectIdeasBox");
  const aiList = document.getElementById("aiProjectIdeasList");
  const starterBox = document.getElementById("starterCodeBox");
  const starterList = document.getElementById("starterProjectsList");

  // AI Ideas section
  if (aiBox && aiList) {
    if (aiProjects && aiProjects.length > 0) {
      aiBox.classList.remove("hidden");
      aiList.innerHTML = aiProjects
        .map((idea) => `<li>${idea}</li>`)
        .join("");
    } else {
      aiBox.classList.add("hidden");
      aiList.innerHTML = "";
    }
  }

  // Practice Projects + YouTube links
  if (projectContainer) {
    const projectsHTML = recommendedProjects
      .map((p) => {
        const videos = p.videos || [];
        const videosHTML =
          videos.length > 0
            ? `
          <div class="mt-3 border-t border-slate-700/70 pt-2">
            <p class="text-[11px] text-slate-300 mb-1">🎥 Watch & Learn</p>
            <ul class="space-y-1 text-[11px]">
              ${videos
                .map(
                  (v) => `
                <li>
                  <a href="${v.url}" target="_blank" class="text-cyan-300 hover:underline">
                    ${v.title}
                  </a>
                  <span class="text-slate-400"> · ${v.channel}</span>
                </li>
              `
                )
                .join("")}
            </ul>
          </div>
        `
            : "";

        return `
        <div class="hover:bg-slate-800/70 p-4 rounded-xl border border-slate-700/80 transition hover:-translate-y-[2px]">
          <h4 class="text-sm font-bold text-cyan-200">${p.skill}</h4>
          <p class="text-slate-200 text-[12px] mt-1">${p.project}</p>
          ${videosHTML}
        </div>
      `;
      })
      .join("");

    projectContainer.innerHTML =
      projectsHTML ||
      '<p class="text-slate-300 text-sm">No skill-based project suggestions available.</p>';
  }

  // Starter Code packs
  if (starterBox && starterList) {
    if (!starterProjects || starterProjects.length === 0) {
      starterBox.classList.add("hidden");
      starterList.innerHTML = "";
    } else {
      starterBox.classList.remove("hidden");
      starterList.innerHTML = starterProjects
        .map((zipPath) => {
          const filename = zipPath.split(/[\\/]/).pop();
          return `
          <div class="bg-purple-950/40 p-4 rounded-xl border border-purple-500/60 flex justify-between items-center transition hover:bg-purple-900/60">
            <div class="flex items-center gap-3">
              <div class="text-2xl">📦</div>
              <div>
                <h4 class="text-sm font-bold text-purple-100">Starter Code: ${filename}</h4>
              </div>
            </div>
            <a href="${zipBase}${filename}" download="${filename}"
               class="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 text-white px-4 py-2 rounded-lg text-[11px] font-bold shadow-lg shadow-purple-500/40">
              Download
            </a>
          </div>
        `;
        })
        .join("");
    }
  }

  // E) Skill chart: match vs missing
  const chartCanvas = document.getElementById("skillChart");
  if (chartCanvas) {
    const totalRequired =
      requiredSkillsAI.length > 0
        ? requiredSkillsAI.length
        : userSkills.length + missingSkills.length;
    const missingCount = missingSkills.length;
    const matched = Math.max(totalRequired - missingCount, 0);

    const ctx = chartCanvas.getContext("2d");
    if (skillChartInstance) {
      skillChartInstance.destroy();
    }

    skillChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Matched Skills", "Missing Skills"],
        datasets: [
          {
            data: [matched, missingCount],
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#e5e7eb", font: { size: 11 } },
          },
        },
      },
    });
  }
}

// Resume upload handler
async function uploadResume() {
  const fileInput = document.getElementById("resumeUpload");
  const file = fileInput.files[0];
  if (!file) {
    alert("Please choose a PDF resume first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${BASE_URL}/api/upload_resume`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload resume");
    const data = await res.json();

    if (data.extracted_skills && Array.isArray(data.extracted_skills)) {
      const skillsInput = document.getElementById("skills");
      const manual = skillsInput.value
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s);
      const merged = [...new Set([...manual, ...data.extracted_skills])];
      skillsInput.value = merged.join(", ");
      alert("✅ Skills extracted from resume!");
    } else {
      alert("No clear skills found in resume.");
    }
  } catch (err) {
    console.error("Error uploading resume:", err);
    alert("Failed to extract skills from resume.");
  }
}
