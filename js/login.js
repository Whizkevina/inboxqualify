document.addEventListener('DOMContentLoaded', () => {
    // API base URL (update if your backend is deployed elsewhere)
    const API_BASE_URL = 'http://127.0.0.1:8000';

    // Form and button elements
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const showLoginBtn = document.getElementById('show-login');
    const showSignupBtn = document.getElementById('show-signup');
    const messageDiv = document.getElementById('auth-message');

    // Toggle between login and signup forms
    showLoginBtn.addEventListener('click', () => {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        showLoginBtn.classList.add('active');
        showSignupBtn.classList.remove('active');
        messageDiv.textContent = '';
    });

    showSignupBtn.addEventListener('click', () => {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        showLoginBtn.classList.remove('active');
        showSignupBtn.classList.add('active');
        messageDiv.textContent = '';
    });

    // Handle Signup Form Submission
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Signup failed');
            }

            messageDiv.textContent = 'Account created successfully! Please log in.';
            messageDiv.style.color = 'var(--green)';
            signupForm.reset();
            showLoginBtn.click(); // Switch to login form

        } catch (error) {
            messageDiv.textContent = `Error: ${error.message}`;
            messageDiv.style.color = 'var(--red)';
        }
    });

    // Handle Login Form Submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON
            const formData = new URLSearchParams();
            formData.append('username', email); // The form uses 'username' for the email field
            formData.append('password', password);

            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
            
            // On successful login, save the token and redirect
            localStorage.setItem('accessToken', data.access_token);
            window.location.href = '/'; // Redirect to the main app page

        } catch (error) {
            messageDiv.textContent = `Error: ${error.message}`;
            messageDiv.style.color = 'var(--red)';
        }
    });
});