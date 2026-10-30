// auth.js - login and register, connected to the Flask API
let isLogin = true;

const title = document.getElementById('form-title');
const btn = document.getElementById('submit-btn');
const confirmGroup = document.getElementById('confirm-group');
const switchPrefix = document.getElementById('switch-prefix');
const switchLink = document.getElementById('switch-link');
const message = document.getElementById('message');
const form = document.getElementById('auth-form');

function showMessage(text, type) {
  message.textContent = text;
  message.className = 'message ' + (type || '');
}

function render() {
  title.textContent = isLogin ? 'Login' : 'Register';
  btn.textContent = isLogin ? 'Login' : 'Create Account';
  confirmGroup.style.display = isLogin ? 'none' : 'block';
  switchPrefix.textContent = isLogin ? 'New here?' : 'Already have an account?';
  switchLink.textContent = isLogin ? 'Create an account' : 'Login';
  showMessage('', '');
}

switchLink.addEventListener('click', (e) => {
  e.preventDefault();
  isLogin = !isLogin;
  render();
});

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  return { ok: res.ok, data: data };
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const confirmPw = document.getElementById('confirm').value;

  if (!isLogin && password !== confirmPw) {
    showMessage('Passwords do not match.', 'error');
    return;
  }

  btn.disabled = true;
  showMessage(isLogin ? 'Logging in...' : 'Creating account...', 'success');

  try {
    const url = isLogin ? '/api/login' : '/api/register';
    const result = await postJson(url, { username: username, password: password });
    if (result.ok) {
      window.location.href = '/dashboard.html';
    } else {
      showMessage(result.data.error || 'Something went wrong.', 'error');
      btn.disabled = false;
    }
  } catch (err) {
    showMessage('Cannot reach the server. Is app.py running?', 'error');
    btn.disabled = false;
  }
});

render();