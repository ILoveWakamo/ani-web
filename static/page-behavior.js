/* ========================
   Custom Video Player Logic
   ======================== */
document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("video");
    const container = document.getElementById("playerContainer");

    // If this page has no video player, stop here
    if (!video || !container) return;

    const playPause = document.getElementById("playPause");
    const rewind = document.getElementById("rewind");
    const forward = document.getElementById("forward");
    const seekBar = document.getElementById("seekBar");
    const fullscreen = document.getElementById("fullscreen");
    const timestamp = document.getElementById("timestamp");

    const playIcon = playPause.querySelector(".play");
    const pauseIcon = playPause.querySelector(".pause");

    /* Play / Pause */
    function togglePlay() {
        if (video.paused) {
            video.play();
            playIcon.classList.add("hidden");
            pauseIcon.classList.remove("hidden");
        } else {
            video.pause();
            playIcon.classList.remove("hidden");
            pauseIcon.classList.add("hidden");
        }
    }

    playPause.addEventListener("click", togglePlay);
    video.addEventListener("click", () => {
        const controlsVisible = window.getComputedStyle(container.querySelector(".controls-bar")).opacity === "1";
        if (controlsVisible) {
            togglePlay();
        }
    });

    /* Update seek bar */
    video.addEventListener("timeupdate", () => {
        if (!video.duration) return;
        seekBar.value = (video.currentTime / video.duration) * 100;
        timestamp.innerHTML = parseInt((video.currentTime / 60) % 60).toLocaleString('en-US', {
            minimumIntegerDigits: 2,
            useGrouping: false
        })
            + ":" + parseInt(video.currentTime % 60).toLocaleString('en-US', {
                minimumIntegerDigits: 2,
                useGrouping: false
            });
    });

    /* Seek */
    seekBar.addEventListener("input", () => {
        if (!video.duration) return;
        video.currentTime = (seekBar.value / 100) * video.duration;
    });

    document.addEventListener("keydown", (e) => {
        if (e.code === "ArrowRight") {
            video.currentTime = Math.min(video.currentTime + 10, video.duration);
        } else if (e.code === "ArrowLeft") {
            video.currentTime = Math.max(video.currentTime - 10, 0);
        }
    });

    /* Skip backward / forward */
    rewind.addEventListener("click", () => {
        video.currentTime = Math.max(video.currentTime - 88, 0);
    });

    forward.addEventListener("click", () => {
        video.currentTime = Math.min(video.currentTime + 88, video.duration);
    });

    /* Fullscreen */
    fullscreen.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });

    /* Sync icons if playback ends */
    video.addEventListener("ended", () => {
        playIcon.classList.remove("hidden");
        pauseIcon.classList.add("hidden");
    });

    let hideControlsTimeout;

    /* Render controls visible*/
    function showControls() {
        container.querySelector(".controls-bar").style.opacity = "1";
    }

    /* Render controls invisible*/
    function hideControls() {
        container.querySelector(".controls-bar").style.opacity = "0";
    }

    /* Define timeout to hide controls*/
    function resetControlsTimer() {
        showControls();
        clearTimeout(hideControlsTimeout);
        hideControlsTimeout = setTimeout(() => {
            hideControls();
        }, 2500); // 2.5 seconds
    }

    // Show controls on mousemove or touch
    container.addEventListener("mousemove", resetControlsTimer);
    container.addEventListener("touchstart", resetControlsTimer);

    const speedBtn = document.getElementById("speedBtn");
    const speedMenu = document.getElementById("speedMenu");
    const speedOptions = speedMenu.querySelectorAll("button");

    let currentSpeed = 1;
    video.playbackRate = currentSpeed;

    // Toggle menu
    speedBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        speedMenu.style.display =
            speedMenu.style.display === "block" ? "none" : "block";
    });

    // Select speed
    speedOptions.forEach(btn => {
        btn.addEventListener("click", () => {
            const speed = parseFloat(btn.dataset.speed);
            video.playbackRate = speed;
            currentSpeed = speed;

            speedOptions.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            speedMenu.style.display = "none";
        });
    });

    // Close menu when clicking elsewhere
    document.addEventListener("click", () => {
        speedMenu.style.display = "none";
    });

    // Initialize
    resetControlsTimer();

});




/* ========================
Schedule page interactions
======================== */

function horizontal_scroll(event) {
    event.preventDefault();
    if (recent.scrollWidth > recent.clientWidth) {
        event.preventDefault();
        recent.scrollLeft += event.deltaY;
    }
    { passive: false }
}

const recent = document.querySelector('.recent-episodes');
if (recent) {
    recent.onwheel = horizontal_scroll;
}
/* ========================
Mode switch buttons (sub/dub)
======================== */


document.addEventListener("DOMContentLoaded", () => {
    console.log("content is loaded");
    document.querySelectorAll(".mode-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const mode = btn.dataset.mode;
            const url = new URL(window.location);
            const title = btn.dataset.title

            console.log("switching to " + mode);
            if (title) {
                url.searchParams.set("title", title);
            }
            url.searchParams.set("mode", mode);
            window.location = url;
        });
    });
});

/* ========================
   Watchlist functionality
======================== */
document.addEventListener("DOMContentLoaded", () => {

    const WATCHLIST_KEY = 'aniweb_watchlist';

    // Get the watchlist array from localStorage
    function getWatchlist() {
        const stored = localStorage.getItem(WATCHLIST_KEY);
        return stored ? JSON.parse(stored) : [];
    }

    // Save watchlist
    function saveWatchlist(list) {
        localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
    }

    // Check if anime is in watchlist
    function isInWatchlist(anime) {
        return getWatchlist().includes(anime);
    }

    // Toggle anime in watchlist
    function toggleWatchlist(anime) {
        let watchlist = getWatchlist();
        if (watchlist.includes(anime)) {
            watchlist = watchlist.filter(id => id !== anime);
        } else {
            watchlist.push(anime);
        }
        saveWatchlist(watchlist);
        updateWatchlistButtons();
    }

    // Update all watchlist buttons
    function updateWatchlistButtons() {
        //for schedule and search page
        document.querySelectorAll('.watchlist-btn').forEach(btn => {
            const anime = btn.dataset.anime;
            btn.textContent = isInWatchlist(anime) ? '★' : '☆';
            if (btn.textContent == '☆' && btn.classList[1] === "remove-btn") {
                btn.parentElement.remove();
            }

        });

        //for description page
        var btn = document.getElementById("description-watchlist-btn")
        if (btn) {
            const anime = btn.dataset.anime;
            btn.textContent = isInWatchlist(anime) ? 'Remove from watchlist' : 'Add to watchlist';
        }

    }

    // Attach click event to buttons
    document.querySelectorAll('.watchlist-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault(); // prevent card navigation
            const anime = btn.dataset.anime;
            toggleWatchlist(anime);
        });
    });
    var btn = document.getElementById("description-watchlist-btn");
    btn.addEventListener('click', e => {
        const anime = btn.dataset.anime;
        toggleWatchlist(anime);
    })


    // Initialize stars on page load
    updateWatchlistButtons();

    // Select the element you want to watch
    const target = document.getElementById('watchlist-grid');

    if (target) {
        // Create observer
        const observer = new MutationObserver((mutationsList, observer) => {
            for (const mutation of mutationsList) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    document.querySelectorAll('.watchlist-btn').forEach(btn => {
                        btn.addEventListener('click', e => {
                            e.preventDefault(); // prevent card navigation
                            const anime = btn.dataset.anime;
                            toggleWatchlist(anime);
                        });
                    });
                    updateWatchlistButtons();
                    console.log("mutations deteced")
                }
            }
        });
        observer.observe(target, {
            childList: true,       // watch adding/removing children
        });
    }


});





