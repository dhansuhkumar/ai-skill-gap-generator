let skillChartInstance = null; // Global chart instance

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('recommendForm');
  const loading = document.getElementById('loading');
  const results = document.getElementById('results');

  // 🧠 Handle form submission for recommendations
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    results.classList.add('hidden');
    loading.classList.remove('hidden');

    const skills = document.getElementById('skills').value.split(',').map(s => s.trim());
    const role = document.getElementById('role').value;
    const user_id = document.getElementById('user_id')?.value || "dhanush123";
    fetch("http://127.0.0.1:5000/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: "dhanush", password: "test123" })
})
.then(res => res.json())
.then(data => {
  localStorage.setItem("jwtToken", data.token);
});

    try {
      // 🔹 Step 1: Get recommendations
      const response = await fetch('http://127.0.0.1:5000/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, skills })
      });

      const data = await response.json();

      // 🔒 Step 2: Save profile
    const token = localStorage.getItem("jwtToken");

await fetch("http://127.0.0.1:5000/api/save_profile", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify({
    role: "developer",
    skills: ["python", "flask"],
    recommendations: ["learn docker", "build flask app"]
  })
});


      // 🟡 Missing Skills
      document.getElementById('missingSkills').innerHTML =
        `<div class="mb-4 p-4 bg-yellow-100 text-yellow-800 rounded-lg shadow">
           <h3 class="font-semibold text-lg mb-2">⚠️ Missing Skills</h3>
           <ul class="list-disc list-inside">${data.missing_skills.map(skill => `<li>${skill}</li>`).join('')}</ul>
         </div>`;

      // 🔵 Recommended Projects
      document.getElementById('recommendedProjects').innerHTML =
        `<div class="mb-4 p-4 bg-blue-100 text-blue-800 rounded-lg shadow">
           <h3 class="font-semibold text-lg mb-2">💡 Suggested Projects</h3>
           <ul class="list-disc list-inside">${data.recommended_projects.map(p => `<li>${p.skill}: ${p.project}</li>`).join('')}</ul>
         </div>`;

      // 🟣 Starter Projects
      document.getElementById('starterProjects').innerHTML =
        `<div class="mb-4 p-4 bg-purple-100 text-purple-800 rounded-lg shadow">
           <h3 class="font-semibold text-lg mb-2">🚀 Starter Projects</h3>
           <ul class="list-disc list-inside">${(data.starter_projects || []).map(zip => {
             const filename = zip.split('\\').pop();
             return `<li><a href="file:///${zip.replace(/\\/g, '/')}" download="${filename}" class="underline">${filename}</a></li>`;
           }).join('')}</ul>
         </div>`;

      // 🟢 AI Project Ideas
      if (data.ai_projects && data.ai_projects.length > 0) {
        document.getElementById('ai_projects').innerHTML =
          `<div class="mb-4 p-4 bg-green-100 text-green-800 rounded-lg shadow">
             <h3 class="font-semibold text-lg mb-2">🤖 AI Project Ideas</h3>
             <ul class="list-disc list-inside">${data.ai_projects.map(idea => `<li>${idea}</li>`).join('')}</ul>
           </div>`;
      } else {
        document.getElementById('ai_projects').innerHTML = '';
      }

      // 📊 Skill Coverage Chart
      const allSkills = [...skills, ...data.missing_skills];
      const uniqueSkills = [...new Set(allSkills)];
      const skillLabels = uniqueSkills;
      const skillData = uniqueSkills.map(skill => skills.includes(skill) ? 1 : 0);
      const skillColors = skillData.map(val => val ? '#4ade80' : '#f87171');

      const ctx = document.getElementById('skillChart').getContext('2d');
      if (skillChartInstance) {
        skillChartInstance.destroy();
      }
      skillChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: skillLabels,
          datasets: [{
            label: 'Skill Coverage',
            data: skillData,
            backgroundColor: skillColors
          }]
        },
        options: {
          scales: {
            y: { beginAtZero: true, max: 1 }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });

      // ✅ Show results
      loading.classList.add('hidden');
      results.classList.remove('hidden');
      results.classList.add('transition-opacity', 'duration-500', 'opacity-100');
    } catch (error) {
      loading.classList.add('hidden');
      console.error('Error fetching recommendations:', error);
      alert('Error fetching recommendations.');
    }
  });
});

// 📄 Resume Upload Handler
function uploadResume() {
  const fileInput = document.getElementById("resumeUpload");
  const file = fileInput.files[0];
  if (!file) return alert("Please select a PDF file.");

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  fetch("http://127.0.0.1:5000/api/upload_resume", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      const skills = data.extracted_skills;
      console.log("Extracted skills:", skills);
      document.getElementById("skills").value = skills.join(", ");
    })
    .catch((err) => {
      console.error("Upload failed:", err);
      alert("Resume upload failed.");
    });
}