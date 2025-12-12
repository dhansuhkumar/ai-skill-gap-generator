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
  const results = document.getElementById("results");
  const loginForm = document.getElementById("loginForm");
  const authStatus = document.getElementById("authStatus");
  const logoutButton = document.getElementById("logoutButton");
  const wizardSteps = document.getElementById("wizardSteps");
  const step1Fields = document.getElementById("step1Fields");
  const step2Fields = document.getElementById("step2Fields");
  const nextStepBtn = document.getElementById("nextStepBtn");
  const backStepBtn = document.getElementById("backStepBtn");
  const themeDarkBtn = document.getElementById("themeDark");
  const themeLightBtn = document.getElementById("themeLight");

  let currentStep = 1;

  // Hard gate: if not logged in, send user to login page
  const tokenAtStart = localStorage.getItem("jwtToken");
  const usernameAtStart = localStorage.getItem("username");
  if (!tokenAtStart || !usernameAtStart) {
    // Avoid redirect loop if someone accidentally opens login.html with this script
    const currentPage = window.location.pathname.split("/").pop() || "";
    if (currentPage.toLowerCase() === "index.html" || currentPage === "") {
      window.location.href = "login.html";
      return;
    }
  }

  // Theme handling
  function applyTheme(theme) {
    if (theme === "light") {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
    localStorage.setItem("themePreference", theme);
    if (themeDarkBtn && themeLightBtn) {
      if (theme === "light") {
        themeLightBtn.classList.add("bg-slate-800", "text-slate-100");
        themeDarkBtn.classList.remove("bg-slate-800", "text-slate-100");
      } else {
        themeDarkBtn.classList.add("bg-slate-800", "text-slate-100");
        themeLightBtn.classList.remove("bg-slate-800", "text-slate-100");
      }
    }
  }

  const savedTheme = localStorage.getItem("themePreference") || "dark";
  applyTheme(savedTheme);

  if (themeDarkBtn) {
    themeDarkBtn.addEventListener("click", () => applyTheme("dark"));
  }
  if (themeLightBtn) {
    themeLightBtn.addEventListener("click", () => applyTheme("light"));
  }

  // Wizard step handling
  function setStep(step) {
    currentStep = step;
    if (step1Fields && step2Fields) {
      if (step === 1) {
        step1Fields.classList.remove("hidden");
        step2Fields.classList.add("hidden");
      } else {
        step1Fields.classList.add("hidden");
        step2Fields.classList.remove("hidden");
      }
    }
    if (wizardSteps) {
      const stepNodes = wizardSteps.querySelectorAll("[data-step]");
      stepNodes.forEach((node) => {
        const s = parseInt(node.getAttribute("data-step"), 10);
        const badge = node.querySelector("span.w-6");
        if (!badge) return;
        if (s === step) {
          badge.classList.add("bg-cyan-500", "text-slate-950");
          badge.classList.remove("bg-slate-800", "text-slate-300");
          node.classList.remove("opacity-60");
        } else {
          badge.classList.add("bg-slate-800", "text-slate-300");
          badge.classList.remove("bg-cyan-500", "text-slate-950");
          if (s > step) {
            node.classList.add("opacity-60");
          }
        }
      });
    }
  }

  setStep(1);

  if (nextStepBtn) {
    nextStepBtn.addEventListener("click", () => {
      setStep(2);
    });
  }

  if (backStepBtn) {
    backStepBtn.addEventListener("click", () => {
      setStep(1);
    });
  }

  // Helper: check auth state on load
  function refreshAuthUI() {
    const token = localStorage.getItem("jwtToken");
    const username = localStorage.getItem("username");
    if (token && username) {
      if (authStatus)
        authStatus.textContent = `Logged in as ${username}`;
      if (logoutButton) logoutButton.classList.remove("hidden");
    } else {
      if (authStatus) authStatus.textContent = "Not logged in";
      if (logoutButton) logoutButton.classList.add("hidden");
    }
  }

  refreshAuthUI();

  // Try to load existing profile for the logged-in user
  async function loadUserProfile() {
    const token = localStorage.getItem("jwtToken");
    const username = localStorage.getItem("username");
    if (!token || !username) return;

    try {
      const res = await fetch(`${BASE_URL}/api/profile/${encodeURIComponent(username)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) return;
      const profile = await res.json();

      // Pre-fill inputs if we have data
      const skillsInput = document.getElementById("skills");
      const roleInput = document.getElementById("role");
      if (skillsInput && Array.isArray(profile.skills)) {
        skillsInput.value = profile.skills.join(", ");
      }
      if (roleInput && profile.role) {
        roleInput.value = profile.role;
      }

      // Optionally render last recommendations
      if (profile.recommendations) {
        // Reuse UI renderer with minimal fake structure
        updateUIWithRecommendations(
          { 
            missing_skills: [],
            recommended_projects: profile.recommendations,
            starter_projects: [],
            ai_projects: [],
            required_skills_ai: [],
            job_matches: [],
          },
          profile.role || "",
          profile.skills || []
        );
        const results = document.getElementById("results");
        if (results) results.classList.remove("hidden");
      }
    } catch (e) {
      console.log("Failed to load saved profile (ignored):", e);
    }
  }

  loadUserProfile();

  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      localStorage.removeItem("jwtToken");
      localStorage.removeItem("username");
      refreshAuthUI();
      alert("You have been logged out.");
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const usernameInput = document.getElementById("loginUsername");
      const passwordInput = document.getElementById("loginPassword");
      const username = usernameInput.value.trim();
      const password = passwordInput.value;

      if (!username || !password) {
        alert("Please enter username and password.");
        return;
      }

      try {
        const res = await fetch(`${BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
          alert("Login failed. Check your credentials.");
          return;
        }

        const data = await res.json();
        if (!data.access_token) {
          alert("Login response missing token.");
          return;
        }

        localStorage.setItem("jwtToken", data.access_token);
        localStorage.setItem("username", username);
        refreshAuthUI();
        alert("Logged in successfully!");
        await loadUserProfile();
      } catch (err) {
        console.error("Login error:", err);
        alert("Login error. Please try again.");
      }
    });
  }

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
    // Add single raw profile prompt if user provided it
    const rawProfileEl = document.getElementById("rawProfileInput");
    if (rawProfileEl) {
      const rawText = rawProfileEl.value.trim();
      if (rawText) payload.raw_profile_text = rawText;
    }
    if (includeVideosCheckbox && includeVideosCheckbox.checked) {
      payload.include_youtube = true;
      // Use the exact key your backend checks for
      payload.max_video_results = parseInt(
        document.getElementById("maxVideoResults")?.value || "3",
        10
      );
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

      const token = localStorage.getItem("jwtToken");
      const username = localStorage.getItem("username");
      if (token && username) {
        fetch(`${BASE_URL}/api/save_profile`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            role,
            skills,
            recommendations: data.recommended_projects || [],
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
      // hide generate button wrapper if present
      const genWrapHide = document.getElementById("generateProjectsWrapper");
      if (genWrapHide) genWrapHide.classList.add("hidden");
    } else {
      // Render selectable checkboxes for missing skills (checked by default)
      missingContainer.innerHTML = missingSkills
        .map((skill, idx) => {
          const priority = idx < 2 ? "High impact" : idx < 5 ? "Medium impact" : "Nice to have";
          return `
        <label class="flex items-center gap-2 bg-rose-500/15 text-rose-200 border border-rose-500/40 px-3 py-1 rounded-full text-[11px] font-medium cursor-pointer">
          <input type="checkbox" class="missing-skill-checkbox" value="${skill}" checked />
          <span class="ml-1">${skill}</span>
          <span class="ml-2 text-[9px] font-semibold uppercase tracking-wide px-2 py-[2px] rounded-full bg-rose-500/30 text-rose-100 border border-rose-300/60">
            ${priority}
          </span>
        </label>
      `;
        })
        .join("");

      // Show generate button
      const genWrap = document.getElementById("generateProjectsWrapper");
      if (genWrap) genWrap.classList.remove("hidden");

      // Attach click handler for the generate button
      const genBtn = document.getElementById("generateProjectsBtn");
      if (genBtn) {
        genBtn.onclick = async function () {
          const checkboxes = Array.from(document.querySelectorAll('.missing-skill-checkbox'));
          const selected = checkboxes.filter(c => c.checked).map(c => c.value);
          if (!selected || selected.length === 0) {
            alert('Please select at least one skill to generate projects for.');
            return;
          }

          // Build payload for /recommend/projects
          const rawProfileEl = document.getElementById('rawProfileInput');
          const includeVideosCheckbox = document.getElementById('includeVideos');
          const payload = { selected_missing_skills: selected };
          if (rawProfileEl && rawProfileEl.value.trim()) payload.raw_profile_text = rawProfileEl.value.trim();
          if (includeVideosCheckbox && includeVideosCheckbox.checked) {
            payload.include_youtube = true;
            payload.max_video_results = parseInt(document.getElementById('maxVideoResults')?.value || '3', 10);
          }

          try {
            genBtn.disabled = true;
            genBtn.textContent = 'Generating...';
            const res = await fetch(`${BASE_URL}/recommend/projects`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error('Failed to generate projects');
            const json = await res.json();
            const projects = json.recommended_projects || [];

            // Render returned projects into the project container (reuse existing UI structure)
            const projectContainer = document.getElementById('projectContainer');
            if (projectContainer) {
              const palette = [
                { cardBg: 'bg-gradient-to-r from-cyan-950/80 to-cyan-800/80', cardBorder: 'border-cyan-400/70', badgeBg: 'bg-cyan-500/20', badgeText: 'text-cyan-200', badgeBorder: 'border-cyan-400/60' },
                { cardBg: 'bg-gradient-to-r from-emerald-950/80 to-emerald-800/80', cardBorder: 'border-emerald-400/70', badgeBg: 'bg-emerald-500/20', badgeText: 'text-emerald-200', badgeBorder: 'border-emerald-400/60' },
                { cardBg: 'bg-gradient-to-r from-amber-950/80 to-amber-800/80', cardBorder: 'border-amber-400/70', badgeBg: 'bg-amber-500/20', badgeText: 'text-amber-100', badgeBorder: 'border-amber-400/60' },
              ];

              const projectsHTML = projects.map((p, idx) => {
                const colors = palette[idx % palette.length];
                const videos = p.videos || [];
                const steps = p.learning_path_steps || [];
                const stepsHTML = steps.length > 0 ? `<div class="mt-3 border-t border-slate-700/70 pt-2"><p class="text-sm text-white mb-2">📚 Learning Path</p><div class="grid grid-cols-1 gap-2">${steps.map((s, idx) => `<div class="flex items-start gap-2 rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2"><span class="mt-[1px] inline-flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500 text-[11px] font-bold text-slate-950">${idx+1}</span><p class="text-sm text-white/90 leading-snug">${s}</p></div>`).join('')}</div></div>` : '';
                const videosHTML = videos.length > 0 ? `<div class="mt-3 border-t border-slate-700/70 pt-2"><p class="text-sm text-white mb-2">🎥 Watch & Learn</p><div class="grid grid-cols-1 gap-2">${videos.map(v => `<a href="${v.url}" target="_blank" class="flex items-center justify-between rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2 hover:border-cyan-400 hover:bg-slate-900/80 transition"><div class="flex flex-col"><span class="text-sm font-semibold text-cyan-200 line-clamp-1">${v.title}</span><span class="text-[11px] text-white/70">${v.channel}</span></div><span class="text-sm text-cyan-200 font-semibold">▶</span></a>`).join('')}</div></div>` : '';

                return `<div class="p-4 md:p-5 rounded-xl border ${colors.cardBg} ${colors.cardBorder} transition hover:-translate-y-[2px] hover:shadow-lg hover:shadow-cyan-500/20"><div class="flex items-center justify-between mb-1"><h4 class="text-base font-bold text-white">${p.skill}</h4><span class="text-[11px] px-2 py-[2px] rounded-full ${colors.badgeBg} ${colors.badgeText} ${colors.badgeBorder}">Focus skill</span></div><p class="text-white/90 text-sm mt-2 leading-snug">${p.project}</p>${stepsHTML}${videosHTML}</div>`;
              }).join('');

              projectContainer.innerHTML = projectsHTML || '';
            }

            genBtn.textContent = 'Generate Projects for Selected Skills';
          } catch (err) {
            console.error('Error generating projects:', err);
            alert('Failed to generate projects: ' + err.message);
            genBtn.textContent = 'Generate Projects for Selected Skills';
          } finally {
            genBtn.disabled = false;
          }
        };
      }
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

      const topToFocus = missingSkills.slice(0, 3);
      const focusText =
        topToFocus.length > 0
          ? `Focus on <span class="font-semibold">${topToFocus.join(
              ", "
            )}</span> next to move this closer to 100%.`
          : "You’re very close – keep practicing and refining your portfolio projects.";

      jobFitSummary.innerHTML = `
        <span class="text-[11px] text-slate-200">
          You match <span class="font-semibold">${primary.known_count}</span> of
          <span class="font-semibold">${primary.total_required}</span> core skills for this role.
          ${focusText}
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
    const palette = [
      {
        cardBg: "bg-gradient-to-r from-cyan-950/80 to-cyan-800/80",
        cardBorder: "border-cyan-400/70",
        badgeBg: "bg-cyan-500/20",
        badgeText: "text-cyan-200",
        badgeBorder: "border-cyan-400/60",
      },
      {
        cardBg: "bg-gradient-to-r from-emerald-950/80 to-emerald-800/80",
        cardBorder: "border-emerald-400/70",
        badgeBg: "bg-emerald-500/20",
        badgeText: "text-emerald-200",
        badgeBorder: "border-emerald-400/60",
      },
      {
        cardBg: "bg-gradient-to-r from-amber-950/80 to-amber-800/80",
        cardBorder: "border-amber-400/70",
        badgeBg: "bg-amber-500/20",
        badgeText: "text-amber-100",
        badgeBorder: "border-amber-400/60",
      },
      {
        cardBg: "bg-gradient-to-r from-rose-950/80 to-rose-800/80",
        cardBorder: "border-rose-400/70",
        badgeBg: "bg-rose-500/20",
        badgeText: "text-rose-200",
        badgeBorder: "border-rose-400/60",
      },
      {
        cardBg: "bg-gradient-to-r from-purple-950/80 to-purple-800/80",
        cardBorder: "border-purple-400/70",
        badgeBg: "bg-purple-500/20",
        badgeText: "text-purple-200",
        badgeBorder: "border-purple-400/60",
      },
    ];

    const projectsHTML = recommendedProjects
      .map((p, idx) => {
        const colors = palette[idx % palette.length];
        const videos = p.videos || [];
        const steps = p.learning_path_steps || [];
        const stepsHTML =
          steps.length > 0
            ? `
          <div class="mt-3 border-t border-slate-700/70 pt-2">
            <p class="text-sm text-white mb-2">📚 Learning Path</p>
            <div class="grid grid-cols-1 gap-2">
              ${steps
                .map(
                  (s, idx) => `
                <div class="flex items-start gap-2 rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2">
                  <span class="mt-[1px] inline-flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500 text-[11px] font-bold text-slate-950">
                    ${idx + 1}
                  </span>
                  <p class="text-sm text-white/90 leading-snug">${s}</p>
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : "";
        const videosHTML =
          videos.length > 0
            ? `
          <div class="mt-3 border-t border-slate-700/70 pt-2">
            <p class="text-sm text-white mb-2">🎥 Watch & Learn</p>
            <div class="grid grid-cols-1 gap-2">
              ${videos
                .map(
                  (v) => `
                <a href="${v.url}" target="_blank"
                   class="flex items-center justify-between rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2 hover:border-cyan-400 hover:bg-slate-900/80 transition">
                  <div class="flex flex-col">
                    <span class="text-sm font-semibold text-cyan-200 line-clamp-1">${v.title}</span>
                    <span class="text-[11px] text-white/70">${v.channel}</span>
                  </div>
                  <span class="text-sm text-cyan-200 font-semibold">▶</span>
                </a>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : "";

        return `
        <div class="p-4 md:p-5 rounded-xl border ${colors.cardBg} ${colors.cardBorder} transition hover:-translate-y-[2px] hover:shadow-lg hover:shadow-cyan-500/20">
          <div class="flex items-center justify-between mb-1">
            <h4 class="text-base font-bold text-white">${p.skill}</h4>
            <span class="text-[11px] px-2 py-[2px] rounded-full ${colors.badgeBg} ${colors.badgeText} ${colors.badgeBorder}">
              Focus skill
            </span>
          </div>
          <p class="text-white/90 text-sm mt-2 leading-snug">${p.project}</p>
          ${stepsHTML}
          ${videosHTML}
        </div>
      `;
      })
      .join("");

    projectContainer.innerHTML = projectsHTML || "";
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
