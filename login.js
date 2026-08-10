// login.js - handles client-side validation for login and signup forms

document.addEventListener('DOMContentLoaded', function () {

    // ---------- Password show/hide toggle ---------- //
    document.querySelectorAll('.toggle-password').forEach(function (icon) {
        icon.addEventListener('click', function () {
            const targetId = icon.getAttribute('data-target') || 'password';
            const input = document.getElementById(targetId);
            if (!input) return;
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye-slash-fill');
                icon.classList.add('bi-eye-fill');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-fill');
                icon.classList.add('bi-eye-slash-fill');
            }
        });
    });

    // ---------- Login form validation ---------- //
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            let valid = true;

            const emailError = document.getElementById('emailError');
            const passwordError = document.getElementById('passwordError');
            emailError.textContent = '';
            passwordError.textContent = '';

            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(email)) {
                emailError.textContent = 'Please enter a valid email address.';
                valid = false;
            }
            if (password.length < 1) {
                passwordError.textContent = 'Password is required.';
                valid = false;
            }
            if (!valid) e.preventDefault();
        });
    }

    // ---------- Signup form validation ---------- //
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const strengthDisplay = document.getElementById('passwordStrength');
        const matchError = document.getElementById('matchError');

        passwordInput.addEventListener('input', function () {
            const val = passwordInput.value;
            let strength = 'weak';
            let label = 'Weak password';

            if (val.length >= 8 && /[A-Za-z]/.test(val) && /[0-9]/.test(val) && /[^A-Za-z0-9]/.test(val)) {
                strength = 'strong';
                label = 'Strong password';
            } else if (val.length >= 6 && /[A-Za-z]/.test(val) && /[0-9]/.test(val)) {
                strength = 'medium';
                label = 'Medium strength';
            }

            strengthDisplay.textContent = val.length ? label : '';
            strengthDisplay.className = 'password-strength ' + strength;
        });

        signupForm.addEventListener('submit', function (e) {
            let valid = true;
            matchError.textContent = '';

            if (passwordInput.value !== confirmInput.value) {
                matchError.textContent = 'Passwords do not match.';
                valid = false;
            }
            if (passwordInput.value.length < 6 || !/[0-9]/.test(passwordInput.value) || !/[A-Za-z]/.test(passwordInput.value)) {
                matchError.textContent = 'Password must be at least 6 characters with letters and numbers.';
                valid = false;
            }
            if (!valid) e.preventDefault();
        });
    }
});
