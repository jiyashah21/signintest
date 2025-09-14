
  // Get user info from localStorage
  const loginBtn = document.getElementById('loginBtn');
  const userName = localStorage.getItem('userName');

  if (userName) {
      // Replace the button text with user's name
      loginBtn.textContent = userName;

      // Optional: Disable click since already logged in
      loginBtn.onclick = null;

      // Optional: add a dropdown or logout later
      loginBtn.style.cursor = 'default';
  }



async function fetchNotices() {
    try {
        const res = await fetch("https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml");
        const text = await res.text();

        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "text/xml");

        const items = xml.querySelectorAll("item");
        const container = document.getElementById("notices-list");
        container.innerHTML = "";

        items.forEach(item => {
            const title = item.querySelector("title").textContent;
            const link = item.querySelector("link").textContent;

            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = link;
            a.textContent = title;
            a.target = "_blank";
            li.appendChild(a);
            container.appendChild(li);
        });
    } catch (err) {
        console.error("Error fetching RSS:", err);
        document.getElementById("notices-list").innerHTML = "<li>Failed to load notices</li>";
    }
}

// Initial fetch
fetchNotices();

// Refresh every 5 minutes
setInterval(fetchNotices, 300000);

window.addEventListener('DOMContentLoaded', () => {
  const iframe = document.getElementById('weather-widget-frame');
  // Optionally check if widget supports detect location param
  // If worried about user blocking, you could add timeout then change src
  setTimeout(() => {
    // if still blank or error, load default
    if (!iframe.src || iframe.src.includes("geoloc=detect")) {
      // Fallback embed using a fixed city (e.g. Chennai)
      iframe.src = "https://www.meteoblue.com/en/weather/widget/daily/chennai_india?tempunit=°C";
    }
  }, 5000); // 5 seconds wait
});
