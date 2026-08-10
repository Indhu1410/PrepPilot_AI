// interview.js - drives the AI interview experience:
// fetching questions, timer, voice input/output, submitting answers,
// showing AI feedback, and handling attempts / progression.

let currentIndex = 0;
let currentAttempt = 1;
let seconds = 0;
let timerInterval = null;
let recognizing = false;
let recognition = null;

const questionText = document.getElementById('questionText');
const qNumberBadge = document.getElementById('qNumberBadge');
const attemptsBadge = document.getElementById('attemptsBadge');
const answerBox = document.getElementById('answerBox');
const submitBtn = document.getElementById('submitBtn');
const nextBtn = document.getElementById('nextBtn');
const feedbackBox = document.getElementById('feedbackBox');
const scorePill = document.getElementById('scorePill');
const fbCorrectness = document.getElementById('fbCorrectness');
const fbGrammar = document.getElementById('fbGrammar');
const fbConfidence = document.getElementById('fbConfidence');
const fbSuggestions = document.getElementById('fbSuggestions');
const correctAnswerBox = document.getElementById('correctAnswerBox');
const correctAnswerText = document.getElementById('correctAnswerText');
const progressBar = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const loadingScreen = document.getElementById('loadingScreen');
const questionCard = document.getElementById('questionCard');
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');
const timerDisplay = document.getElementById('timerDisplay');

// ---------------- Timer ---------------- //
function startTimer() {
    clearInterval(timerInterval);
    seconds = 0;
    timerInterval = setInterval(function () {
        seconds++;
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        timerDisplay.textContent = `${m}:${s}`;
    }, 1000);
}

// ---------------- Text to Speech ---------------- //
function speakQuestion(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
}

// ---------------- Speech Recognition ---------------- //
function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        micStatus.textContent = 'Voice input not supported in this browser. Please type your answer.';
        micBtn.disabled = true;
        return;
    }
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = function () {
        recognizing = true;
        micBtn.classList.add('recording');
        micStatus.textContent = 'Listening... speak your answer now.';
    };

    recognition.onresult = function (event) {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        answerBox.value = transcript;
    };

    recognition.onerror = function () {
        micStatus.textContent = 'Could not capture audio. Please try again or type your answer.';
    };

    recognition.onend = function () {
        recognizing = false;
        micBtn.classList.remove('recording');
        micStatus.textContent = 'Click the mic to speak, or type below';
    };
}

micBtn?.addEventListener('click', function () {
    if (!recognition) return;
    if (recognizing) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

// ---------------- Question Loading ---------------- //
function loadQuestion() {
    feedbackBox.classList.add('d-none');
    correctAnswerBox.classList.add('d-none');
    nextBtn.classList.add('d-none');
    submitBtn.classList.remove('d-none');
    answerBox.value = '';
    answerBox.disabled = false;
    currentAttempt = 1;

    fetch('/api/get_question')
        .then(res => res.json())
        .then(data => {
            if (data.done) {
                window.location.href = '/finish_interview';
                return;
            }
            currentIndex = data.index;
            questionText.textContent = data.question;
            qNumberBadge.textContent = `Q${data.index + 1}`;
            attemptsBadge.textContent = `Attempt 1 / ${MAX_ATTEMPTS}`;

            const pct = Math.round((data.index / data.total) * 100);
            progressBar.style.width = pct + '%';
            progressLabel.textContent = `Question ${data.index + 1} of ${data.total}`;

            startTimer();
            speakQuestion(data.question);
        });
}

// ---------------- Submit Answer ---------------- //
submitBtn?.addEventListener('click', function () {
    const answer = answerBox.value.trim();
    if (!answer) {
        alert('Please provide an answer before submitting (type or use the microphone).');
        return;
    }

    submitBtn.disabled = true;
    questionCard.classList.add('d-none');
    loadingScreen.classList.remove('d-none');

    fetch('/api/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answer, attempt: currentAttempt })
    })
    .then(res => res.json())
    .then(data => {
        loadingScreen.classList.add('d-none');
        questionCard.classList.remove('d-none');
        submitBtn.disabled = false;

        const evalData = data.evaluation;
        scorePill.textContent = evalData.score + '%';
        fbCorrectness.textContent = evalData.correctness;
        fbGrammar.textContent = evalData.grammar;
        fbConfidence.textContent = evalData.confidence;
        fbSuggestions.textContent = evalData.suggestions;
        feedbackBox.classList.remove('d-none');

        if (data.show_correct_answer && data.correct_answer) {
            correctAnswerText.textContent = data.correct_answer;
            correctAnswerBox.classList.remove('d-none');
        }

        if (data.advance) {
            submitBtn.classList.add('d-none');
            nextBtn.classList.remove('d-none');
            answerBox.disabled = true;
        } else {
            currentAttempt++;
            attemptsBadge.textContent = `Attempt ${currentAttempt} / ${MAX_ATTEMPTS}`;
            answerBox.value = '';
        }
    })
    .catch(() => {
        loadingScreen.classList.add('d-none');
        questionCard.classList.remove('d-none');
        submitBtn.disabled = false;
        alert('Something went wrong evaluating your answer. Please try again.');
    });
});

nextBtn?.addEventListener('click', function () {
    loadQuestion();
});

// ---------------- Init ---------------- //
document.addEventListener('DOMContentLoaded', function () {
    setupSpeechRecognition();
    loadQuestion();
});
