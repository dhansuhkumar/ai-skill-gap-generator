// frontend/script.js

// Auto-detect backend URL
const isLocal =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.protocol === "file:";

const BASE_URL = isLocal
  ? "http://localhost:5000"
  : "https://your-production-backend.com";
let skillChartInstance = null;
function updateUIWithRecommendations(data, role, userSkills) {
  const requiredSkillsAI = data.required_skills || data.required_skills_ai || [];
  const missingSkills = data.missing_skills || data.missingSkills || [];
  const aiProjects = data.ai_projects || data.aiProjects || [];
  const recommendedProjects =
    data.recommended_projects || data.recommendedProjects || [];
  const starterProjects = data.starter_projects || data.starterProjects || [];

  // Missing skills
  const missingContainer = document.getElementById("missingSkillsList");
  if (missingContainer) {
    if (!missingSkills || missingSkills.length === 0) {
      missingContainer.innerHTML =
        '<span class="text-emerald-300 text-xs">No missing skills detected.</span>';
      const genWrapHide = document.getElementById("generateProjectsWrapper");
      if (genWrapHide) genWrapHide.classList.add("hidden");
    } else {
      missingContainer.innerHTML = missingSkills
        .map(
          (s, i) => `
                    <label class="flex items-center gap-2 bg-rose-500/15 text-rose-200 border border-rose-500/40 px-3 py-1 rounded-full text-[11px] font-medium cursor-pointer">
                      <input type="checkbox" class="missing-skill-checkbox" value="${s}" checked />
                      <span class="ml-1">${s}</span>
                      <span class="ml-2 text-[9px] font-semibold uppercase tracking-wide px-2 py-[2px] rounded-full bg-rose-500/30 text-rose-100 border border-rose-300/60">
                        ${i < 2 ? "High" : i < 5 ? "Medium" : "Low"}
                      </span>
                    </label>`
        )
        .join("");
      const genWrap = document.getElementById("generateProjectsWrapper");
      if (genWrap) genWrap.classList.remove("hidden");

      const genBtn = document.getElementById("generateProjectsBtn");
      if (genBtn) {
        genBtn.onclick = async () => {
          const selected = Array.from(
            document.querySelectorAll(".missing-skill-checkbox")
          )
            .filter((c) => c.checked)
            .map((c) => c.value);
          if (!selected.length) return alert("Select at least one skill");

          const payload = { selected_missing_skills: selected };
          const rawProfileEl = document.getElementById("rawProfileInput");
          if (rawProfileEl && rawProfileEl.value.trim())
            payload.raw_profile_text = rawProfileEl.value.trim();
          const includeVideosCheckbox = document.getElementById("includeVideos");
          if (includeVideosCheckbox && includeVideosCheckbox.checked) {
            payload.include_youtube = true;
            payload.max_video_results_per_skill = parseInt(
              document.getElementById("maxVideoResults")?.value || "3",
              10
            );
          }
          const aiProviderSelect = document.getElementById("aiProviderSelect");
          if (aiProviderSelect && aiProviderSelect.value)
            payload.ai_provider = aiProviderSelect.value;

          try {
            genBtn.disabled = true;
            genBtn.textContent = "Generating...";
            const res = await fetch(`${BASE_URL}/recommend/projects`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error("Failed to generate projects");
            const json = await res.json();
            const projects =
              json.recommended_projects || json.recommendedProjects || [];
            renderProjectCards(projects);
          } catch (err) {
            console.error(err);
            alert("Generating projects failed");
          } finally {
            genBtn.disabled = false;
            genBtn.textContent = "Generate Projects for Selected Skills";
          }
        };
      }
    }
  }

  // AI Ideas
  const aiBox = document.getElementById("aiProjectIdeasBox");
  const aiList = document.getElementById("aiProjectIdeasList");
  if (aiBox && aiList) {
    if (aiProjects && aiProjects.length) {
      aiBox.classList.remove("hidden");
      aiList.innerHTML = aiProjects.map((a) => `<li>${a}</li>`).join("");
    } else {
      aiBox.classList.add("hidden");
      aiList.innerHTML = "";
    }
  }

  // Starter packs
  const starterBox = document.getElementById("starterCodeBox");
  const starterList = document.getElementById("starterProjectsList");
  if (starterBox && starterList) {
    if (!starterProjects || !starterProjects.length) {
      starterBox.classList.add("hidden");
      starterList.innerHTML = "";
    } else {
      starterBox.classList.remove("hidden");
      starterList.innerHTML = starterProjects
        .map((p) => {
          const filename = p.split(/[\\\/]/).pop();
          return `<div class="bg-purple-950/40 p-4 rounded-xl border border-purple-500/60 flex justify-between items-center"><div class="flex items-center gap-3"><div class="text-2xl">📦</div><div><h4 class="text-sm font-bold text-purple-100">Starter Code: ${filename}</h4></div></div><a href="${zipBase}${filename}" download="${filename}" class="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg text-[11px] font-bold">Download</a></div>`;
        })
        .join("");
    }
  }

  // Render recommended projects into cards
  function renderProjectCards(projects) {
    const projectContainer = document.getElementById("projectContainer");
    if (!projectContainer) return;
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
    ];

    const html = projects
      .map((p, idx) => {
        const colors = palette[idx % palette.length];
        const videos = p.videos || p.video_results || [];
        const steps = p.learning_path_steps || p.learningPath || p.steps || [];
        const stepsHTML = steps.length
          ? `<div class="mt-3 border-t border-slate-700/70 pt-2"><p class="text-sm text-white mb-2">📚 Learning Path</p><div class="grid grid-cols-1 gap-2">${steps
              .map(
                (s, i) =>
                  `<div class="flex items-start gap-2 rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2"><span class="mt-[1px] inline-flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500 text-[11px] font-bold text-slate-950">
                    ${i + 1}
                  </span><p class="text-sm text-white/90 leading-snug">${s}</p></div>`
              )
              .join("")}
          </div></div>`
          : "";
        const videosHTML = videos.length
          ? `<div class="mt-3 border-t border-slate-700/70 pt-2"><p class="text-sm text-white mb-2">🎥 Watch & Learn</p><div class="grid grid-cols-1 gap-2">${videos
              .map(
                (v) =>
                  `<a href="${v.url || v.link}" target="_blank" class="flex items-center justify-between rounded-lg bg-slate-950/60 border border-slate-700/70 px-3 py-2"><div class="flex flex-col"><span class="text-sm font-semibold text-cyan-200 line-clamp-1">${v.title || v.video_title}</span><span class="text-[11px] text-white/70">${v.channel || v.channelTitle || ""}</span></div><span class="text-sm text-cyan-200 font-semibold">▶</span></a>`
              )
              .join("")}
          </div></div>`
          : "";
        return `<div class="p-4 md:p-5 rounded-xl border ${colors.cardBg} ${colors.cardBorder}"><div class="flex items-center justify-between mb-1"><h4 class="text-base font-bold text-white">${p.skill || p.focus || "Project"}</h4><span class="text-[11px] px-2 py-[2px] rounded-full ${colors.badgeBg} ${colors.badgeText} ${colors.badgeBorder}">Focus skill</span></div><p class="text-white/90 text-sm mt-2 leading-snug">${p.project || p.description || ""}</p>${stepsHTML}${videosHTML}</div>`;
      })
      .join("");

    projectContainer.innerHTML = html || "";
  }

  // Initial render of recommended projects (if any)
  if (recommendedProjects && recommendedProjects.length)
    renderProjectCards(recommendedProjects);

  // Skill chart
  const chartCanvas = document.getElementById("skillChart");
  if (chartCanvas) {
    const totalRequired =
      requiredSkillsAI && requiredSkillsAI.length
        ? requiredSkillsAI.length
        : userSkills.length + (missingSkills.length || 0);
    const missingCount = missingSkills.length || 0;
    const matched = Math.max(totalRequired - missingCount, 0);
    const ctx = chartCanvas.getContext("2d");
    if (skillChartInstance) skillChartInstance.destroy();
    skillChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Matched Skills", "Missing Skills"],
        datasets: [{ data: [matched, missingCount] }],
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
async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await fetch(`${BASE_URL}/upload/resume`, {
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
      const merged = Array.from(new Set([...manual, ...data.extracted_skills.map(s => s.trim())]));
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