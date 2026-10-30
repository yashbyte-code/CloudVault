// dashboard.js - upload, list, download and delete, connected to the Flask API
let files = [];

const list = document.getElementById('file-list');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const message = document.getElementById('message');
const progress = document.getElementById('progress');
const bar = document.getElementById('progress-bar');
const uploadBtn = document.getElementById('upload-btn');

function showMessage(text, type) {
  message.textContent = text;
  message.className = 'message ' + (type || '');
}

// stops file names from being treated as HTML
function esc(s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function goToLogin() {
  window.location.href = '/login.html';
}

function renderFiles() {
  if (files.length === 0) {
    list.innerHTML = '<tr><td colspan="5" class="empty">No files yet. Upload your first file above.</td></tr>';
    return;
  }
  list.innerHTML = files.map(function (f) {
    return '<tr>' +
      '<td>' + esc(f.name) + ' <span class="badge">🔒 Encrypted</span></td>' +
      '<td>' + formatSize(f.size) + '</td>' +
      '<td>' + f.chunks + '</td>' +
      '<td>' + formatDate(f.created_at) + '</td>' +
      '<td>' +
        '<button class="btn btn-outline btn-small" data-action="download" data-id="' + esc(f.id) + '">Download</button>' +
        '<button class="btn btn-danger btn-small" data-action="delete" data-id="' + esc(f.id) + '">Delete</button>' +
      '</td>' +
    '</tr>';
  }).join('');
}

async function loadFiles(showDone) {
  try {
    const res = await fetch('/api/files');
    if (res.status === 401) { goToLogin(); return; }
    const data = await res.json();
    files = data.files;
    renderFiles();
    if (showDone) showMessage('List refreshed.', 'success');
  } catch (err) {
    showMessage('Cannot reach the server. Is app.py running?', 'error');
  }
}

async function deleteFile(id) {
  const f = files.find(function (x) { return x.id === id; });
  if (!f) return;
  if (!confirm('Delete "' + f.name + '"? This cannot be undone.')) return;
  try {
    const res = await fetch('/api/files/' + encodeURIComponent(id), { method: 'DELETE' });
    if (res.status === 401) { goToLogin(); return; }
    const data = await res.json();
    if (res.ok) {
      showMessage('File deleted.', 'success');
      loadFiles(false);
    } else {
      showMessage(data.error || 'Delete failed.', 'error');
    }
  } catch (err) {
    showMessage('Delete failed. Is app.py running?', 'error');
  }
}

// buttons inside the table
list.addEventListener('click', function (e) {
  const button = e.target.closest('button[data-action]');
  if (!button) return;
  const id = button.dataset.id;
  if (button.dataset.action === 'download') {
    window.location.href = '/api/files/' + encodeURIComponent(id) + '/download';
  } else if (button.dataset.action === 'delete') {
    deleteFile(id);
  }
});

document.getElementById('choose-btn').addEventListener('click', function () { fileInput.click(); });

fileInput.addEventListener('change', function () {
  fileName.textContent = fileInput.files.length ? fileInput.files[0].name : 'No file selected';
});

uploadBtn.addEventListener('click', function () {
  if (!fileInput.files.length) {
    showMessage('Please choose a file first.', 'error');
    return;
  }
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/files');

  xhr.upload.onprogress = function (e) {
    if (e.lengthComputable) bar.style.width = Math.round((e.loaded / e.total) * 100) + '%';
  };

  xhr.onload = function () {
    progress.style.display = 'none';
    uploadBtn.disabled = false;
    if (xhr.status === 401) { goToLogin(); return; }
    let data = {};
    try { data = JSON.parse(xhr.responseText); } catch (err) {}
    if (xhr.status === 201) {
      fileInput.value = '';
      fileName.textContent = 'No file selected';
      showMessage('Upload successful!', 'success');
      loadFiles(false);
    } else {
      showMessage(data.error || 'Upload failed.', 'error');
    }
  };

  xhr.onerror = function () {
    progress.style.display = 'none';
    uploadBtn.disabled = false;
    showMessage('Upload failed. Is app.py running?', 'error');
  };

  bar.style.width = '0%';
  progress.style.display = 'block';
  uploadBtn.disabled = true;
  showMessage('Uploading and encrypting...', 'success');
  xhr.send(formData);
});

document.getElementById('refresh-btn').addEventListener('click', function () { loadFiles(true); });

document.getElementById('logout-btn').addEventListener('click', async function (e) {
  e.preventDefault();
  try { await fetch('/api/logout', { method: 'POST' }); } catch (err) {}
  goToLogin();
});

loadFiles(false);