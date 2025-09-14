document.addEventListener("DOMContentLoaded", () => {
  const getLocBtn = document.getElementById("getLocation");
  const latField = document.getElementById("latitude");
  const lonField = document.getElementById("longitude");
  const form = document.getElementById("reportForm");

  // ------------------ Auto-fill Location ------------------
  if (getLocBtn) {
    getLocBtn.addEventListener("click", () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            latField.value = pos.coords.latitude.toFixed(6);
            lonField.value = pos.coords.longitude.toFixed(6);
          },
          (err) => {
            alert("Unable to fetch location. Please allow location access.");
            console.error(err);
          }
        );
      } else {
        alert("Geolocation is not supported by your browser.");
      }
    });
  }

  // ------------------ Basic Validation ------------------
  if (form) {
    form.addEventListener("submit", (e) => {
      const hazard = document.getElementById("hazard_type").value.trim();
      const desc = document.getElementById("description").value.trim();
      const city = document.getElementById("city").value.trim();

      if (!hazard || !desc || !city) {
        e.preventDefault();
        alert("Please fill in all required fields (Hazard, Description, City).");
        return;
      }
    });
  }
});
