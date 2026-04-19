const API_URL = "http://127.0.0.1:5000/api";

// --- DOM Elements ---
const authSection = document.getElementById("auth-section");
const feedSection = document.getElementById("feed-section");
const profileSection = document.getElementById("profile-section");
const adminSection = document.getElementById("admin-section");

const loginForm = document.getElementById("login-form");
const createPostForm = document.getElementById("create-post-form");
const fileInput = document.getElementById("file-upload");
const fileNameDisplay = document.getElementById("file-name-display");

const logoutBtn = document.getElementById("logout-btn");
const navFeedBtn = document.getElementById("nav-feed-btn");
const navProfileBtn = document.getElementById("nav-profile-btn");
const navAdminBtn = document.getElementById("nav-admin-btn");
const themeBtn = document.getElementById("theme-toggle-btn");

const authToggleLink = document.getElementById("show-register");
const authTitle = document.querySelector("#auth-section h3");
const authBtn = document.getElementById("auth-submit-btn");

const loadPostsBtn = document.getElementById("load-posts-btn");
const loadMyPostsBtn = document.getElementById("load-my-posts-btn");
const postsContainer = document.getElementById("posts-container");
const myPostsContainer = document.getElementById("my-posts-container");
const errorText = document.getElementById("login-error");

// Modal Elements
const editProfileModal = document.getElementById("edit-profile-modal");
const editProfileBtn = document.getElementById("edit-profile-btn");
const closeModalBtn = document.getElementById("close-modal-btn");
const editProfileForm = document.getElementById("edit-profile-form");

// Search & Pagination Elements
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const clearSearchBtn = document.getElementById("clear-search-btn");
const loadMoreBtn = document.getElementById("load-more-btn");
const noMorePostsText = document.getElementById("no-more-posts-text");

let isLoginMode = true;
let currentPage = 1;
let currentSearchQuery = "";

// --- Helpers ---
function parseJwt(token) {
    try { return JSON.parse(atob(token.split('.')[1])); } catch (e) { return null; }
}

function getCurrentUser() {
    const token = localStorage.getItem("peerview_token");
    return token ? parseJwt(token) : null;
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("peerview_token");
    if (token) showFeed();

    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
        if(themeBtn) themeBtn.textContent = "☀️ Light Mode";
    }
});

// --- Authentication ---
if (authToggleLink) {
    authToggleLink.addEventListener("click", (e) => {
        e.preventDefault();
        isLoginMode = !isLoginMode;
        if(authTitle) authTitle.textContent = isLoginMode ? "Welcome Back" : "Create Account";
        if(authBtn) authBtn.textContent = isLoginMode ? "Sign In" : "Register";
        authToggleLink.textContent = isLoginMode ? "Sign Up" : "Back to Login";
    });
}

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if(errorText) errorText.classList.add("hidden");

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const endpoint = isLoginMode ? "/auth/login" : "/auth/register";

        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (response.ok) {
                if (isLoginMode) {
                    localStorage.setItem("peerview_token", data.token);
                    showFeed();
                } else {
                    alert("Account created! Please log in.");
                    isLoginMode = true;
                    authToggleLink.click();
                }
            } else {
                if(errorText) {
                    errorText.textContent = data.message;
                    errorText.classList.remove("hidden");
                } else {
                    alert(data.message);
                }
            }
        } catch (err) {
            if(errorText) {
                errorText.textContent = "Server connection failed.";
                errorText.classList.remove("hidden");
            }
        }
    });
}

// --- Post Creation ---
if (createPostForm) {
    createPostForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const contentBox = document.getElementById("new-post-content");
        const token = localStorage.getItem("peerview_token");

        const formData = new FormData();
        formData.append("content", contentBox.value);
        formData.append("post_type", "blog");
        if (fileInput && fileInput.files[0]) {
            formData.append("file", fileInput.files[0]);
        }

        try {
            const response = await fetch(`${API_URL}/posts`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });
            if (response.ok) {
                contentBox.value = "";
                if(fileInput) fileInput.value = "";
                if(fileNameDisplay) fileNameDisplay.textContent = "";

                // Clear any search and fetch fresh feed (page 1)
                if (searchInput) searchInput.value = "";
                if(loadPostsBtn) loadPostsBtn.click();
            } else {
                const data = await response.json();
                alert(`Error: ${data.message}`);
            }
        } catch (err) { alert("Post failed. Make sure the server is running."); }
    });
}

if (fileInput) {
    fileInput.addEventListener("change", () => {
        if (fileNameDisplay) fileNameDisplay.textContent = fileInput.files[0] ? fileInput.files[0].name : "";
    });
}

// --- Edit Profile Logic ---
if (editProfileBtn) {
    editProfileBtn.addEventListener("click", () => {
        const currentBio = document.getElementById("profile-bio").textContent;
        document.getElementById("edit-bio").value = currentBio;
        if(editProfileModal) editProfileModal.classList.remove("hidden");
    });
}

if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
        if(editProfileModal) editProfileModal.classList.add("hidden");
    });
}

if (editProfileForm) {
    editProfileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("peerview_token");
        const bioText = document.getElementById("edit-bio").value;
        const avatarFile = document.getElementById("edit-avatar").files[0];

        const formData = new FormData();
        formData.append("bio", bioText);
        if (avatarFile) formData.append("avatar", avatarFile);

        try {
            const response = await fetch(`${API_URL}/auth/profile`, {
                method: "PUT",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (response.ok) {
                if(editProfileModal) editProfileModal.classList.add("hidden");
                showProfile();
            } else {
                const data = await response.json();
                alert(`Error: ${data.message}`);
            }
        } catch (err) { alert("Failed to update profile."); }
    });
}

// --- Post Rendering ---
function createPostHTML(post) {
    let mediaHtml = "";
    if (post.file_path) {
        const fullUrl = `http://127.0.0.1:5000${post.file_path}`;
        if (post.file_path.match(/\.(jpg|jpeg|png|gif)$/i)) {
            mediaHtml = `<img src="${fullUrl}" style="width:100%; border-radius:8px; margin:10px 0; border: 1px solid var(--border);">`;
        } else if (post.file_path.endsWith('.pdf')) {
            mediaHtml = `
                <div style="background:var(--bg-color); padding:15px; border-radius:8px; margin:10px 0; display:flex; align-items:center; gap:10px; border: 1px solid var(--border);">
                    <span style="font-size:1.5rem;">📄</span>
                    <div style="flex:1">
                        <p style="font-size:0.9rem; font-weight:600; margin:0;">Document Attached</p>
                        <a href="${fullUrl}" target="_blank" style="font-size:0.8rem; color:var(--primary); text-decoration:none;">View PDF</a>
                    </div>
                </div>`;
        }
    }

    const currentUpvotes = post.upvotes !== undefined ? post.upvotes : 0;
    const currentDownvotes = post.downvotes !== undefined ? post.downvotes : 0;

    const currentUser = getCurrentUser();
    let deleteBtnHtml = "";
    if (currentUser && (currentUser.role === 'admin' || currentUser.user_id === post.author_id)) {
        deleteBtnHtml = `<button onclick="window.deletePost(${post.id})" class="secondary-btn" style="color:red; border-color:red; padding:2px 8px; font-size:0.75rem;">Delete</button>`;
    }

    return `
        <div class="post-content">${post.content}</div>
        ${mediaHtml}
        <div class="post-meta" style="display:flex; justify-content:space-between; border-top:1px solid var(--border); padding-top:10px; margin-top:10px;">
            <span>Post ID: ${post.id}</span>
            ${deleteBtnHtml}
        </div>
        
        <div style="margin-top:15px; display:flex; align-items:center; gap:20px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <button onclick="window.castVote(${post.id}, 1)" class="secondary-btn" style="padding: 5px 10px;">👍</button>
                <span style="font-size: 1.1rem; font-weight: bold; color: #16a34a;">${currentUpvotes}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <button onclick="window.castVote(${post.id}, -1)" class="secondary-btn" style="padding: 5px 10px;">👎</button>
                <span style="font-size: 1.1rem; font-weight: bold; color: #dc2626;">${currentDownvotes}</span>
            </div>
        </div>

        <div id="comments-container-${post.id}" style="margin-top:10px;">
            <button onclick="window.loadComments(${post.id}, ${post.author_id})" class="secondary-btn" style="width:100%;">View Reviews</button>
        </div>
        <div style="display:flex; gap:5px; margin-top:5px;">
            <input type="text" id="comment-input-${post.id}" placeholder="Review..." style="flex:1; padding:8px; border-radius:6px; border:1px solid var(--border); background:var(--card-bg); color:var(--text-main);">
            <button onclick="window.postComment(${post.id}, ${post.author_id})" class="primary-btn" style="width:auto; padding:5px 10px;">Send</button>
        </div>
    `;
}

// --- Feed Loading & Pagination ---
async function fetchAndRenderFeed(searchQuery = "", page = 1) {
    try {
        let url = `${API_URL}/posts?page=${page}`;
        if (searchQuery) {
            url += `&q=${encodeURIComponent(searchQuery)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        // If this is page 1, completely clear the old posts out
        if (page === 1) {
            postsContainer.innerHTML = "";
            currentPage = 1;
            currentSearchQuery = searchQuery;
            if(noMorePostsText) noMorePostsText.classList.add("hidden");
        }

        if (data.data.length === 0 && page === 1) {
            postsContainer.innerHTML = `<p style="padding: 1rem; color: var(--text-muted);">No posts found.</p>`;
            if(loadMoreBtn) loadMoreBtn.classList.add("hidden");
            return;
        }

        // Draw the new posts
        data.data.forEach(post => {
            const el = document.createElement("div");
            el.className = "post-card";
            el.innerHTML = createPostHTML(post);
            postsContainer.appendChild(el);
        });

        // Hide or show the "Load More" button depending on how many posts came back
        if (data.data.length < 5) { // 5 is our limit from the backend
            if(loadMoreBtn) loadMoreBtn.classList.add("hidden");
            if(noMorePostsText && postsContainer.innerHTML !== "") noMorePostsText.classList.remove("hidden");
        } else {
            if(loadMoreBtn) loadMoreBtn.classList.remove("hidden");
            if(noMorePostsText) noMorePostsText.classList.add("hidden");
        }
    } catch (err) { console.error("Feed load error:", err); }
}

// "Load More" Button Click
if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", () => {
        currentPage++;
        fetchAndRenderFeed(currentSearchQuery, currentPage);
    });
}

if (loadPostsBtn) {
    loadPostsBtn.addEventListener("click", () => fetchAndRenderFeed(searchInput ? searchInput.value : "", 1));
}

if (searchBtn) {
    searchBtn.addEventListener("click", () => {
        const query = searchInput ? searchInput.value.trim() : "";
        fetchAndRenderFeed(query, 1);
    });
}

if (searchInput) {
    searchInput.addEventListener("keyup", (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            fetchAndRenderFeed(query, 1);
        }
    });
}

if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        fetchAndRenderFeed("", 1); // Fetch all posts again from page 1
    });
}

// --- Profile Posts Loading ---
if (loadMyPostsBtn) {
    loadMyPostsBtn.addEventListener("click", async () => {
        const token = localStorage.getItem("peerview_token");
        try {
            const response = await fetch(`${API_URL}/posts/me`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await response.json();
            myPostsContainer.innerHTML = "";

            if (data.data.length === 0) {
                myPostsContainer.innerHTML = "<p style='padding:1rem;'>You haven't posted anything yet.</p>";
                return;
            }

            data.data.forEach(post => {
                const el = document.createElement("div");
                el.className = "post-card";
                el.innerHTML = createPostHTML(post);
                myPostsContainer.appendChild(el);
            });
        } catch (err) { console.error("Profile load error:", err); }
    });
}

// --- Navigation ---
function showFeed() {
    [authSection, profileSection, adminSection].forEach(s => { if(s) s.classList.add("hidden"); });
    if(feedSection) feedSection.classList.remove("hidden");
    [logoutBtn, navFeedBtn, navProfileBtn].forEach(b => { if(b) b.classList.remove("hidden"); });

    const token = localStorage.getItem("peerview_token");
    if (token) {
        const user = parseJwt(token);
        if (user && user.role === 'admin' && navAdminBtn) {
            navAdminBtn.classList.remove("hidden");
        }
    }
    if(loadPostsBtn) loadPostsBtn.click();
}

async function showProfile() {
    [authSection, feedSection, adminSection].forEach(s => { if(s) s.classList.add("hidden"); });
    if(profileSection) profileSection.classList.remove("hidden");

    const token = localStorage.getItem("peerview_token");

    try {
        const response = await fetch(`${API_URL}/auth/profile`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await response.json();

        if (response.ok) {
            const profileUsername = document.getElementById("profile-username");
            const profileRole = document.getElementById("profile-role");
            const profileBio = document.getElementById("profile-bio");
            const avatarDiv = document.getElementById("profile-avatar");

            if (profileUsername) profileUsername.textContent = data.data.username;
            if (profileRole) profileRole.textContent = data.data.role.toUpperCase();
            if (profileBio) profileBio.textContent = data.data.bio;

            if (avatarDiv) {
                if (data.data.avatar_url) {
                    avatarDiv.innerHTML = `<img src="http://127.0.0.1:5000${data.data.avatar_url}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
                } else {
                    avatarDiv.innerHTML = data.data.username.charAt(0).toUpperCase();
                }
            }
        }
    } catch (err) { console.error("Failed to load profile details", err); }

    if(loadMyPostsBtn) loadMyPostsBtn.click();
}

function showAdmin() {
    [authSection, feedSection, profileSection].forEach(s => { if(s) s.classList.add("hidden"); });
    if(adminSection) adminSection.classList.remove("hidden");
    fetchStats();
    window.loadReports();
}

function showAuth() {
    [feedSection, profileSection, adminSection, logoutBtn, navFeedBtn, navProfileBtn, navAdminBtn].forEach(el => { if(el) el.classList.add("hidden"); });
    if(authSection) authSection.classList.remove("hidden");
    if(loginForm) loginForm.reset();
}

if(navFeedBtn) navFeedBtn.addEventListener("click", showFeed);
if(navProfileBtn) navProfileBtn.addEventListener("click", showProfile);
if(navAdminBtn) navAdminBtn.addEventListener("click", showAdmin);
if(logoutBtn) logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("peerview_token");
    showAuth();
});

if (themeBtn) {
    themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        const isDark = document.body.classList.contains("dark-mode");
        themeBtn.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
        localStorage.setItem("theme", isDark ? "dark" : "light");
    });
}

// --- Global Functions ---
window.castVote = async (postId, voteType) => {
    const token = localStorage.getItem("peerview_token");
    try {
        const response = await fetch(`${API_URL}/interactions/votes`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ post_id: postId, vote_type: voteType })
        });

        if (response.ok) {
            const feedSection = document.getElementById("feed-section");
            if (feedSection && !feedSection.classList.contains("hidden")) {
                if(loadPostsBtn) loadPostsBtn.click();
            } else {
                if(loadMyPostsBtn) loadMyPostsBtn.click();
            }
        } else {
            const data = await response.json();
            alert(data.message);
        }
    } catch (e) { console.error(e); }
};

window.loadComments = async (postId, postAuthorId) => {
    const container = document.getElementById(`comments-container-${postId}`);
    if(!container) return;

    const token = localStorage.getItem("peerview_token");
    const currentUser = getCurrentUser();

    try {
        const response = await fetch(`${API_URL}/interactions/posts/${postId}/comments`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await response.json();

        if(data.data.length === 0) {
            container.innerHTML = `<p style="font-size:0.85rem; color:var(--text-muted); margin-top: 10px;">No reviews yet. Be the first!</p>`;
            return;
        }

        container.innerHTML = data.data.map(c => {
            let actionBtnsHtml = `<button onclick="window.reportComment(${c.id})" style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:0.8rem;" title="Report this review">🚩 Report</button>`;

            if (currentUser && (currentUser.role === 'admin' || currentUser.user_id === postAuthorId)) {
                actionBtnsHtml += `<button onclick="window.deleteComment(${c.id}, ${postId}, ${postAuthorId})" style="background:none; border:none; color:red; cursor:pointer; font-size:0.8rem; margin-left:10px;" title="Delete this review">🗑️ Delete</button>`;
            }

            return `
            <div style="background:var(--bg-color); padding:10px; margin-top:8px; border-radius:6px; font-size:0.85rem; border-left: 3px solid var(--primary);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:var(--text-main); font-weight: 700;">${c.author_display}</strong>
                    <div>${actionBtnsHtml}</div>
                </div>
                <p style="margin: 5px 0 0 0; color:var(--text-muted);">${c.content}</p>
            </div>`;
        }).join('');

    } catch (e) { console.error(e); }
};

window.postComment = async (postId, postAuthorId) => {
    const input = document.getElementById(`comment-input-${postId}`);
    const token = localStorage.getItem("peerview_token");
    if (!input || !input.value) return;
    try {
        await fetch(`${API_URL}/interactions/comments`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ post_id: postId, content: input.value })
        });
        input.value = "";
        window.loadComments(postId, postAuthorId);
    } catch (e) { console.error(e); }
};

window.reportComment = async (commentId) => {
    const token = localStorage.getItem("peerview_token");
    if(!confirm("Report this review to the administrators?")) return;
    try {
        const response = await fetch(`${API_URL}/interactions/comments/${commentId}/report`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await response.json();
        alert(data.message);
    } catch(e) { console.error(e); }
};

window.deleteComment = async (commentId, postId, postAuthorId) => {
    const token = localStorage.getItem("peerview_token");
    if(!confirm("Permanently delete this review from your post?")) return;
    try {
        const response = await fetch(`${API_URL}/interactions/comments/${commentId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await response.json();
        if(response.ok) {
            window.loadComments(postId, postAuthorId);
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch(e) { console.error(e); }
};

// --- Admin Reporting Tools ---
window.loadReports = async () => {
    const token = localStorage.getItem("peerview_token");
    const container = document.getElementById("reported-comments-container");
    if(!container) return;

    try {
        const response = await fetch(`${API_URL}/interactions/comments/reported`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await response.json();

        if (data.data.length === 0) {
            container.innerHTML = "<p style='color: #16a34a; font-weight: bold;'>✓ No reported reviews. The community is safe!</p>";
            return;
        }

        container.innerHTML = data.data.map(r => `
            <div style="border-left: 4px solid #dc2626; background: var(--bg-color); padding: 10px; margin-bottom: 10px; border-radius: 4px;">
                <p style="margin: 0 0 5px 0;"><strong>True Identity:</strong> <span style="color: var(--primary);">${r.real_author}</span></p>
                <p style="margin: 0 0 10px 0; color: var(--text-muted);"><strong>Review:</strong> "${r.content}"</p>
                <div style="display: flex; gap: 10px;">
                    <button onclick="window.deleteComment(${r.id}, ${r.post_id}, 0); setTimeout(window.loadReports, 500);" class="secondary-btn" style="color:red; border-color:red; padding: 5px 10px;">Trash Review</button>
                    <button onclick="window.dismissReport(${r.id})" class="secondary-btn" style="padding: 5px 10px;">Dismiss (It's OK)</button>
                </div>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
};

window.dismissReport = async (commentId) => {
    const token = localStorage.getItem("peerview_token");
    try {
        await fetch(`${API_URL}/interactions/comments/${commentId}/dismiss`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        window.loadReports();
    } catch(e) { console.error(e); }
};

// --- Posts Deletion ---
window.deletePost = async (postId) => {
    if (!confirm("Permanently delete this post?")) return;
    const token = localStorage.getItem("peerview_token");
    try {
        await fetch(`${API_URL}/posts/${postId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        if(loadPostsBtn) loadPostsBtn.click();
        if(loadMyPostsBtn && profileSection && !profileSection.classList.contains("hidden")) loadMyPostsBtn.click();
    } catch (e) { console.error(e); }
};

async function fetchStats() {
    try {
        const pRes = await fetch(`${API_URL}/posts`);
        const pData = await pRes.json();
        const statTotal = document.getElementById("stat-total-posts");
        if(statTotal) statTotal.textContent = pData.data.length;
    } catch (e) { console.error(e); }
}