// ============================================================
// ARC LEARNS - FRONTEND JAVASCRIPT
// PHASE 12
// ============================================================


// ============================================================
// BACKEND URL
// ============================================================

const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : "https://arc-learns-api.onrender.com";

// ============================================================
// TOAST NOTIFICATIONS & COLD START HELPERS
// ============================================================

function showToast(message, type = "info", duration = 5000) {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    const icons = {
        info: "⚡",
        success: "✓",
        warning: "⚠️",
        error: "✕"
    };
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || "•"}</span><span>${escapeHTML(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-exit");
        setTimeout(() => toast.remove(), 350);
    }, duration);
    return toast;
}

function withColdStartNotice(actionName = "Request") {
    let timer = setTimeout(() => {
        showToast("⚡ Initializing ARC AI cloud engine... Render free-tier can take ~30s on cold start.", "info", 9000);
    }, 4500);
    return () => clearTimeout(timer);
}


// ============================================================
// GLOBAL STATE
// ============================================================

let currentSection = "dashboard";

let uploadedFileName = "";

let topicsLearned = 0;

let quizzesTaken = 0;

let totalQuizScore = 0;

let currentQuizTotal = 0;

let currentQuizAnswered = 0;

let currentQuizCorrect = 0;

let missedConcepts = [];

let chatHistory = [];

let arc0History = [];

let isUploading = false;

let isTeaching = false;

let isChatting = false;

let isGeneratingQuiz = false;

let isARC0Busy = false;



// ============================================================
// STUDIO TAB SWITCHING
// ============================================================

function switchStudioTab(tabId, button) {
    const tabs = document.querySelectorAll(".studio-tab-panel");
    tabs.forEach(t => t.classList.remove("active-tab"));
    const target = document.getElementById(tabId);
    if (target) target.classList.add("active-tab");

    const tabBtns = document.querySelectorAll(".studio-tab-btn");
    tabBtns.forEach(b => b.classList.remove("active"));
    if (button) button.classList.add("active");
}

// ============================================================
// SECTION NAVIGATION
// ============================================================

function showSection(sectionId, button = null) {

    const sections =
        document.querySelectorAll(".section");

    sections.forEach(function(section) {

        section.classList.remove(
            "active-section"
        );

    });


    const selectedSection =
        document.getElementById(sectionId);


    if (selectedSection) {

        selectedSection.classList.add(
            "active-section"
        );

    }


    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach(function(item) {

        item.classList.remove("active");

    });


    if (button) {

        button.classList.add("active");

    } else {

        navItems.forEach(function(item) {

            const onclickText =
                item.getAttribute("onclick");


            if (
                onclickText &&
                onclickText.includes(
                    "'" + sectionId + "'"
                )
            ) {

                item.classList.add("active");

            }

        });

    }


    currentSection = sectionId;
    setTimeout(() => {
        if (sectionId === "arc0") document.getElementById("arc0QuestionDirect")?.focus();
        else if (sectionId === "chat") document.getElementById("chatQuestionDirect")?.focus();
        else if (sectionId === "learn") document.getElementById("teachTopicDirect")?.focus();
        else if (sectionId === "quiz") document.getElementById("quizTopicDirect")?.focus();
    }, 50);

    updatePageTitle(sectionId);


    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}


// ============================================================
// PAGE TITLE
// ============================================================

function updatePageTitle(sectionId) {

    const pageTitle =
        document.getElementById("pageTitle");


    if (!pageTitle) {

        return;

    }


    const titles = {
        landing: "ARC LEARN Platform",
        studio: "Integrated Studio Workspace",
        learn: "Interactive AI Teacher",
        chat: "Ask Your Study Material",
        arc0: "ARC Zero — Universal Intelligence",
        quiz: "Turbo Assessment Quiz",
        dashboard: "ARC LEARN Dashboard"
    };


    pageTitle.textContent =
        titles[sectionId] || "ARC LEARNS";

}


// ============================================================
// FILE TYPE HELPERS
// ============================================================

function getFileExtension(fileName) {

    const parts =
        String(fileName)
            .toLowerCase()
            .split(".");


    if (parts.length < 2) {

        return "";

    }


    return parts.pop();

}


function getFileTypeName(fileName) {

    const extension =
        getFileExtension(fileName);


    const names = {

        pdf: "PDF",

        docx: "Word",

        txt: "Text",

        csv: "CSV"

    };


    return names[extension] || "File";

}


function isSupportedFile(file) {

    if (!file) {

        return false;

    }


    const allowedExtensions = ["pdf", "docx", "pptx", "txt", "csv"];


    const extension =
        getFileExtension(file.name);


    return allowedExtensions.includes(
        extension
    );

}


// ============================================================
// UPLOAD STUDY MATERIAL
// Supports PDF / DOCX / TXT / CSV
// ============================================================

async function uploadPDF() {

    const fileInput =
        document.getElementById("pdfFile");


    const status =
        document.getElementById("uploadStatus");


    if (!fileInput) {

        console.error(
            "File input #pdfFile not found."
        );

        return;

    }


    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        showStatus(
            status,
            "Please select a file first.",
            "error"
        );

        return;

    }


    const file =
        fileInput.files[0];


    if (!isSupportedFile(file)) {

        showStatus(
            status,
            "Unsupported file. Please select PDF, Word, TXT or CSV.",
            "error"
        );

        return;

    }


    if (isUploading) {

        return;

    }


    isUploading = true;


    const fileType =
        getFileTypeName(file.name);


    showStatus(
        status,
        "Uploading and processing " +
        fileType +
        " file...",
        "loading"
    );


    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    const clearNotice = withColdStartNotice("Upload");
    try {
        const response =
            await fetch(
                API_BASE + "/upload",
                {

                    method: "POST",

                    body: formData

                }
            );


        if (!response.ok) {

            throw await createAPIError(
                response,
                "Upload failed."
            );

        }


        clearNotice();
        const data =
            await response.json();


        uploadedFileName =
            data.filename ||
            file.name;


        const chapters =
            data.chapters_found || 0;


        const chunks =
            data.total_chunks || 0;


        if (status) {

            status.innerHTML =

                "<strong>✓ " +
                escapeHTML(fileType) +
                " uploaded successfully</strong>" +

                "<br>File: " +
                escapeHTML(
                    uploadedFileName
                ) +

                "<br>Chapters: " +
                chapters +

                "<br>Chunks: " +
                chunks;

            status.style.color =
                "#6ee7aa";

        }


        topicsLearned = 0;

        updateProgress();


        console.log(
            "ARC LEARNS FILE UPLOADED:",
            data
        );


    } catch (error) {
        clearNotice();
        console.error(
            "UPLOAD ERROR:",
            error
        );


        showStatus(
            status,
            "Upload failed: " +
            error.message,
            "error"
        );


    } finally {

        isUploading = false;

    }

}


// ============================================================
// STATUS HELPER
// ============================================================

function showStatus(
    element,
    message,
    type
) {

    if (!element) {

        return;

    }


    element.textContent =
        message;


    if (type === "error") {

        element.style.color =
            "#ff8494";

    }

    else if (type === "loading") {

        element.style.color =
            "#9c89ff";

    }

    else {

        element.style.color =
            "#6ee7aa";

    }

}


// ============================================================
// API ERROR HANDLER
// ============================================================

async function createAPIError(
    response,
    defaultMessage
) {

    let message =
        defaultMessage;


    try {

        clearNotice();
        const data =
            await response.json();


        if (data.detail) {

            if (typeof data.detail === "string") {

                message =
                    data.detail;

            }

            else {

                message =
                    JSON.stringify(
                        data.detail
                    );

            }

        }

        else if (data.error) {

            message =
                data.error;

        }

    } catch (error) {

        // Keep default error.

    }


    return new Error(message);

}


// ============================================================
// AI TEACHER
// ============================================================

async function teachTopic() {
    const topicDirect = document.getElementById("teachTopicDirect");
    const topicStudio = document.getElementById("teachTopic");
    const lenDirect = document.getElementById("teachLengthDirect");
    const lenStudio = document.getElementById("teachLength");
    const outDirect = document.getElementById("lessonOutputDirect");
    const outStudio = document.getElementById("lessonOutput");

    const topic = (
        (topicDirect && topicDirect.value.trim()) ||
        (topicStudio && topicStudio.value.trim()) ||
        ""
    ).trim();

    const length = (
        (lenDirect && lenDirect.value) ||
        (lenStudio && lenStudio.value) ||
        "medium"
    );

    if (topicDirect) topicDirect.value = topic;
    if (topicStudio) topicStudio.value = topic;
    if (lenDirect) lenDirect.value = length;
    if (lenStudio) lenStudio.value = length;

    const outputs = [outDirect, outStudio].filter(Boolean);

    if (!topic) {
        outputs.forEach(out => {
            out.innerHTML = `
                <div class="empty-state">
                    <div>⚠️</div>
                    <h3>Please enter a topic</h3>
                    <p>Enter a topic or select a suggestion above to begin your masterclass.</p>
                </div>
            `;
        });
        showToast("Please enter a topic to learn", "warning");
        return;
    }

    if (isTeaching) return;
    isTeaching = true;

    outputs.forEach(out => {
        out.innerHTML = `
            <div class="empty-state">
                <div class="status-dot-pulse" style="margin: 0 auto 16px auto; width: 24px; height: 24px;"></div>
                <h3>Synthesizing 7-Stage Masterclass...</h3>
                <p>Generating deep pedagogical instruction for <strong>${escapeHTML(topic)}</strong>...</p>
            </div>
        `;
    });

    const clearNotice = withColdStartNotice("AI Teacher");

    try {
        let lessonText = "";
        let streamWorked = false;

        try {
            const response = await fetch(API_BASE + "/teach/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic: topic, length: length })
            });

            if (response.ok && response.body) {
                clearNotice();
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    lessonText += chunk;
                    streamWorked = true;
                    const rendered = `
                        <div class="lesson-content">
                            <div class="lesson-header-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 10px;">
                                <h2 style="margin: 0;">${escapeHTML(topic)}</h2>
                                <button class="pill-chip" onclick="copyLessonText(this)">📋 Copy Lesson</button>
                            </div>
                            ${formatText(lessonText)}
                        </div>
                    `;
                    outputs.forEach(out => {
                        out.innerHTML = rendered;
                        out.scrollTop = out.scrollHeight;
                    });
                }
            }
        } catch (streamErr) {
            console.warn("Teach Stream error, falling back to sync endpoint:", streamErr);
        }

        if (!streamWorked || !lessonText.trim()) {
            const syncRes = await fetch(API_BASE + "/teach", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic: topic, length: length })
            });
            clearNotice();
            if (!syncRes.ok) throw await createAPIError(syncRes, "Unable to generate lesson.");
            const syncData = await syncRes.json();
            lessonText = syncData.lesson || syncData.content || "";
        }

        if (!lessonText.trim()) throw new Error("ARC AI returned an empty lesson.");

        const finalRendered = `
            <div class="lesson-content">
                <div class="lesson-header-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 10px;">
                    <h2 style="margin: 0;">${escapeHTML(topic)}</h2>
                    <div style="display: flex; gap: 8px;">
                        <button class="pill-chip" onclick="copyLessonText(this)">📋 Copy Lesson</button>
                        <button class="pill-chip" onclick="quickFillQuiz('${escapeHTML(topic).replace(/'/g, "\\'")}')">🎯 Test Myself with Quiz</button>
                    </div>
                </div>
                ${formatText(lessonText)}
            </div>
        `;
        outputs.forEach(out => {
            out.innerHTML = finalRendered;
            out.scrollTop = out.scrollHeight;
        });

    } catch (err) {
        clearNotice();
        console.error("Teach Error:", err);
        outputs.forEach(out => {
            out.innerHTML = `
                <div class="empty-state">
                    <div>⚠️</div>
                    <h3>Unable to generate lesson</h3>
                    <p>${escapeHTML(err.message || "Failed to reach AI teacher.")}</p>
                </div>
            `;
        });
        showToast(err.message || "Teacher error", "error");
    } finally {
        isTeaching = false;
    }
}

// ============================================================
// ASK ARC AI / CHAT
// ============================================================

async function sendChat() {
    const inputDirect = document.getElementById("chatQuestionDirect");
    const inputStudio = document.getElementById("chatQuestion");
    const msgDirect = document.getElementById("chatMessagesDirect");
    const msgStudio = document.getElementById("chatMessages");

    const question = (
        (inputDirect && inputDirect.value.trim()) ||
        (inputStudio && inputStudio.value.trim()) ||
        ""
    ).trim();

    if (!question) return;
    if (isChatting) return;

    if (inputDirect) inputDirect.value = "";
    if (inputStudio) inputStudio.value = "";

    const containers = [msgDirect, msgStudio].filter(Boolean);
    containers.forEach(container => {
        const userDiv = document.createElement("div");
        userDiv.className = "message user-message";
        userDiv.innerHTML = `
            <div class="message-content">
                <strong>You</strong>
                <p>${escapeHTML(question)}</p>
            </div>
        `;
        container.appendChild(userDiv);
        container.scrollTop = container.scrollHeight;
    });

    const aiBubbles = [];
    containers.forEach(container => {
        const aiDiv = document.createElement("div");
        aiDiv.className = "message ai-message";
        aiDiv.innerHTML = `
            <div class="message-avatar">A</div>
            <div class="message-content">
                <strong>ARC LEARN Tutor</strong>
                <p class="streaming-text"><span class="loading-pulse">Consulting study material...</span></p>
            </div>
        `;
        container.appendChild(aiDiv);
        container.scrollTop = container.scrollHeight;
        aiBubbles.push(aiDiv);
    });

    isChatting = true;
    const clearNotice = withColdStartNotice("Chat");

    try {
        let answer = "";
        let streamWorked = false;

        try {
            const response = await fetch(API_BASE + "/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    history: chatHistory.slice(-6)
                })
            });

            if (response.ok && response.body) {
                clearNotice();
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    answer += chunk;
                    streamWorked = true;
                    aiBubbles.forEach(aiDiv => {
                        const contentEl = aiDiv.querySelector(".message-content");
                        if (contentEl) {
                            contentEl.innerHTML = `<strong>ARC LEARN Tutor</strong>${formatText(answer)}`;
                        }
                    });
                    containers.forEach(c => c.scrollTop = c.scrollHeight);
                }
            }
        } catch (streamErr) {
            console.warn("Chat Stream error, falling back to sync endpoint:", streamErr);
        }

        if (!streamWorked || !answer.trim()) {
            const syncRes = await fetch(API_BASE + "/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    history: chatHistory.slice(-6)
                })
            });
            clearNotice();
            if (!syncRes.ok) throw await createAPIError(syncRes, "Unable to get an answer.");
            const syncData = await syncRes.json();
            answer = syncData.answer || syncData.response || "";
        }

        if (!answer.trim()) throw new Error("ARC LEARN returned an empty response.");

        aiBubbles.forEach(aiDiv => {
            const contentEl = aiDiv.querySelector(".message-content");
            if (contentEl) {
                contentEl.innerHTML = `<strong>ARC LEARN Tutor</strong>${formatText(answer)}`;
            }
        });
        containers.forEach(c => c.scrollTop = c.scrollHeight);

        chatHistory.push({ role: "user", content: question });
        chatHistory.push({ role: "assistant", content: answer });

    } catch (err) {
        clearNotice();
        console.error("Chat Error:", err);
        aiBubbles.forEach(aiDiv => {
            const contentEl = aiDiv.querySelector(".message-content");
            if (contentEl) {
                contentEl.innerHTML = `<strong>ARC LEARN Tutor</strong><p class="error-msg">⚠️ ${escapeHTML(err.message || "Failed to reach AI service.")}</p>`;
            }
        });
        showToast(err.message || "Chat error", "error");
    } finally {
        isChatting = false;
    }
}

// ============================================================
// ADD CHAT MESSAGE
// ============================================================

function addChatMessage(
    type,
    message
) {

    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (!messages) {

        return null;

    }


    const messageDiv =
        document.createElement(
            "div"
        );


    const id =

        "message-" +

        Date.now() +

        "-" +

        Math.floor(
            Math.random() * 10000
        );


    messageDiv.id = id;


    if (type === "user") {

        messageDiv.className =
            "message user-message";


        messageDiv.innerHTML =

            '<div class="message-content">' +

            '<strong>You</strong>' +

            '<p>' +
            message +
            '</p>' +

            '</div>';


    }

    else {

        messageDiv.className =
            "message ai-message";


        messageDiv.innerHTML =

            '<div class="message-avatar">A</div>' +

            '<div class="message-content">' +

            '<strong>ARC AI</strong>' +

            '<p>' +
            message +
            '</p>' +

            '</div>';

    }


    messages.appendChild(
        messageDiv
    );


    messages.scrollTop =
        messages.scrollHeight;


    return id;

}


// ============================================================
// REMOVE CHAT MESSAGE
// ============================================================

function removeChatMessage(id) {

    if (!id) {

        return;

    }


    const element =
        document.getElementById(id);


    if (element) {

        element.remove();

    }

}


// ============================================================
// CHAT ENTER KEY
// ============================================================

function handleChatKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendChat();

    }

}


// ============================================================
// QUIZ GENERATION
// ============================================================

async function generateQuiz() {
    const topicDirect = document.getElementById("quizTopicDirect");
    const topicStudio = document.getElementById("quizTopic");
    const countDirect = document.getElementById("quizCountDirect");
    const countStudio = document.getElementById("quizQuestionCount");
    const outDirect = document.getElementById("quizOutputDirect");
    const outStudio = document.getElementById("quizOutput");

    const topic = (
        (topicDirect && topicDirect.value.trim()) ||
        (topicStudio && topicStudio.value.trim()) ||
        ""
    ).trim();

    const count = parseInt(
        (countDirect && countDirect.value) ||
        (countStudio && countStudio.value) ||
        "5",
        10
    ) || 5;

    if (topicDirect) topicDirect.value = topic;
    if (topicStudio) topicStudio.value = topic;
    if (countDirect) countDirect.value = count;
    if (countStudio) countStudio.value = count;

    const outputs = [outDirect, outStudio].filter(Boolean);

    if (!topic) {
        outputs.forEach(out => {
            out.innerHTML = `
                <div class="empty-state">
                    <div>⚠️</div>
                    <h3>Please enter a topic</h3>
                    <p>Enter a topic or pick a suggestion above to generate quiz questions.</p>
                </div>
            `;
        });
        showToast("Please enter a topic for the quiz", "warning");
        return;
    }

    if (isGeneratingQuiz) return;
    isGeneratingQuiz = true;

    outputs.forEach(out => {
        out.innerHTML = `
            <div class="empty-state">
                <div class="status-dot-pulse" style="margin: 0 auto 16px auto; width: 24px; height: 24px;"></div>
                <h3>Generating Turbo Quiz...</h3>
                <p>Formulating ${count} interactive questions with distractor analysis for <strong>${escapeHTML(topic)}</strong>...</p>
            </div>
        `;
    });

    const clearNotice = withColdStartNotice("Quiz");

    try {
        const response = await fetch(API_BASE + "/quiz", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic: topic,
                number_of_questions: count
            })
        });
        clearNotice();

        if (!response.ok) throw await createAPIError(response, "Unable to generate quiz.");
        const data = await response.json();

        if (!data.quiz || !Array.isArray(data.quiz) || data.quiz.length === 0) {
            throw new Error("No quiz questions were returned.");
        }

        currentQuiz = data.quiz;
        currentQuizAnswered = 0;
        currentQuizCorrect = 0;

        renderQuiz(data.quiz);

    } catch (err) {
        clearNotice();
        console.error("Quiz Error:", err);
        outputs.forEach(out => {
            out.innerHTML = `
                <div class="empty-state">
                    <div>⚠️</div>
                    <h3>Unable to generate quiz</h3>
                    <p>${escapeHTML(err.message || "Failed to generate quiz.")}</p>
                </div>
            `;
        });
        showToast(err.message || "Quiz error", "error");
    } finally {
        isGeneratingQuiz = false;
    }
}

// ============================================================
// GET QUIZ QUESTION COUNT
// ============================================================

function getQuizQuestionCount() {

    const possibleIds = [

        "quizQuestionCount",

        "questionCount",

        "numberOfQuestions"

    ];


    for (
        let i = 0;
        i < possibleIds.length;
        i++
    ) {

        const element =
            document.getElementById(
                possibleIds[i]
            );


        if (element) {

            let value =
                parseInt(
                    element.value,
                    10
                );


            if (isNaN(value)) {

                value = 5;

            }


            value =
                Math.max(
                    1,
                    Math.min(
                        50,
                        value
                    )
                );


            return value;

        }

    }


    return 5;

}


// ============================================================
// RENDER QUIZ
// ============================================================

function renderQuiz(quiz) {
    const outputs = [
        document.getElementById("quizOutputDirect"),
        document.getElementById("quizOutput")
    ].filter(Boolean);

    if (outputs.length === 0) return;

    outputs.forEach(output => {
        output.innerHTML = "";
        const quizContainer = document.createElement("div");
        quizContainer.className = "quiz-container";

        quiz.forEach(function(item, qIdx) {
            const card = document.createElement("div");
            card.className = "quiz-card";

            const metaRow = document.createElement("div");
            metaRow.className = "quiz-meta-row";
            metaRow.innerHTML = `
                <span class="quiz-number">Q${qIdx + 1}</span>
                <span class="badge-difficulty ${(item.difficulty || "medium").toLowerCase()}">${(item.difficulty || "medium").toUpperCase()}</span>
                ${item.concept_tested ? `<span class="badge-concept">${escapeHTML(item.concept_tested)}</span>` : ""}
            `;
            card.appendChild(metaRow);

            const qTitle = document.createElement("h3");
            qTitle.className = "quiz-question";
            qTitle.textContent = item.question || "Question";
            card.appendChild(qTitle);

            const optionsList = document.createElement("div");
            optionsList.className = "quiz-options";

            const options = item.options || [];
            options.forEach(function(optText, optIdx) {
                const btn = document.createElement("button");
                btn.className = "quiz-option-btn";
                btn.innerHTML = `<span class="option-letter">${String.fromCharCode(65 + optIdx)}</span> <span>${escapeHTML(optText)}</span>`;

                btn.onclick = function() {
                    if (card.dataset.answered === "true") return;
                    card.dataset.answered = "true";

                    const isCorrect = (optText === item.correct_answer) || (item.correct_answer && item.correct_answer.startsWith(String.fromCharCode(65 + optIdx)));

                    const allBtns = optionsList.querySelectorAll(".quiz-option-btn");
                    allBtns.forEach(b => b.disabled = true);

                    if (isCorrect) {
                        btn.classList.add("correct");
                        currentQuizCorrect++;
                    } else {
                        btn.classList.add("incorrect");
                        allBtns.forEach(b => {
                            if (b.innerText.includes(item.correct_answer)) {
                                b.classList.add("correct");
                            }
                        });
                    }

                    const expDiv = document.createElement("div");
                    expDiv.className = "quiz-explanation " + (isCorrect ? "exp-correct" : "exp-incorrect");
                    expDiv.innerHTML = `
                        <strong>${isCorrect ? "✓ Correct!" : "✕ Incorrect"}</strong>
                        <p>${escapeHTML(item.explanation || "Correct answer: " + item.correct_answer)}</p>
                    `;
                    card.appendChild(expDiv);
                };

                optionsList.appendChild(btn);
            });

            card.appendChild(optionsList);
            quizContainer.appendChild(card);
        });

        output.appendChild(quizContainer);
    });
}

function handleQuizAnswer(
    clickedButton,
    selectedAnswer,
    item,
    card
) {
    if (!clickedButton || !card) {
        return;
    }

    // Prevent answering the same question twice
    if (card.dataset.answered === "true") {
        return;
    }
    card.dataset.answered = "true";

    const correctAnswer = item.correct_answer;
    const explanation = item.explanation;
    const distractorAnalysis = item.distractor_analysis || {};

    // Disable all option buttons in this card
    const optionButtons = card.querySelectorAll(".quiz-option, .quiz-option-btn");
    optionButtons.forEach(function(button) {
        button.disabled = true;
        if (button.textContent.trim() === String(correctAnswer).trim()) {
            button.classList.add("correct");
        }
    });

    // Check correctness
    const selected = String(selectedAnswer).trim();
    const correct = String(correctAnswer).trim();

    if (selected === correct) {
        clickedButton.classList.add("correct");
        currentQuizCorrect++;
    } else {
        clickedButton.classList.add("wrong");
        if (item.concept_tested && !missedConcepts.includes(item.concept_tested)) {
            missedConcepts.push(item.concept_tested);
        }
    }

    currentQuizAnswered++;

    // Render In-Depth Pedagogical Explanation
    const explanationDiv = document.createElement("div");
    explanationDiv.className = "quiz-explanation";

    let explanationHtml = "<p><strong>" + (selected === correct ? "✓ Correct!" : "✕ Incorrect.") + "</strong> " + escapeHTML(explanation) + "</p>";

    // Add distractor analysis if available
    if (distractorAnalysis && typeof distractorAnalysis === "object") {
        const distractorKeys = Object.keys(distractorAnalysis);
        if (distractorKeys.length > 0) {
            explanationHtml += "<div class=\"distractor-box\"><strong>Why other options are incorrect:</strong>";
            distractorKeys.forEach(function(optKey) {
                if (optKey.trim() !== correct) {
                    explanationHtml += "<div class=\"distractor-item\">• <em>" + escapeHTML(optKey) + ":</em> " + escapeHTML(distractorAnalysis[optKey]) + "</div>";
                }
            });
            explanationHtml += "</div>";
        }
    }

    explanationDiv.innerHTML = explanationHtml;
    card.appendChild(explanationDiv);

    // If all questions are answered, show performance report
    if (currentQuizAnswered >= currentQuizTotal) {
        quizzesTaken++;
        const quizPercentage = currentQuizTotal > 0 ? (currentQuizCorrect / currentQuizTotal) * 100 : 0;
        totalQuizScore += quizPercentage;
        showQuizResult();
    }

    updateProgress();
}


// ============================================================
// QUIZ RESULT (COMPREHENSIVE RETENTION SUMMARY)
// ============================================================

function showQuizResult() {
    const output = document.getElementById("quizOutput");
    if (!output) return;

    const percentage = currentQuizTotal > 0
        ? Math.round((currentQuizCorrect / currentQuizTotal) * 100)
        : 0;

    let feedbackMsg = "Mastery Demonstrated! Outstanding grasp of the material.";
    if (percentage < 50) {
        feedbackMsg = "Needs Revision. Review the concepts below to solidify your understanding.";
    } else if (percentage < 80) {
        feedbackMsg = "Good Foundation! A few concepts need a quick review.";
    }

    const summaryCard = document.createElement("div");
    summaryCard.className = "quiz-summary-card";

    let summaryHtml = `
        <div class="quiz-score-circle">${percentage}%</div>
        <h3>Score: ${currentQuizCorrect} / ${currentQuizTotal} Questions</h3>
        <p class="quiz-feedback-text">${escapeHTML(feedbackMsg)}</p>
    `;

    if (missedConcepts.length > 0) {
        summaryHtml += `
            <div style="margin-top: 18px;">
                <strong style="color: #cbd5e1; font-size: 13px;">CONCEPTS RECOMMENDED FOR REVISION:</strong>
                <div class="concepts-to-revise">
                    ${missedConcepts.map(c => `<span class="concept-pill">📖 ${escapeHTML(c)}</span>`).join("")}
                </div>
            </div>
        `;
    }

    summaryCard.innerHTML = summaryHtml;
    output.appendChild(summaryCard);
    summaryCard.scrollIntoView({ behavior: "smooth" });
}


// ============================================================
// FORMAT AI TEXT
// ============================================================

function copyCode(button) {
    if (!button) return;
    const pre = button.closest(".code-block");
    if (!pre) return;
    const code = pre.querySelector("code");
    if (!code) return;
    navigator.clipboard.writeText(code.innerText).then(() => {
        const originalText = button.textContent;
        button.textContent = "Copied!";
        button.style.background = "var(--emerald)";
        button.style.color = "#000";
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = "";
            button.style.color = "";
        }, 1800);
    }).catch(err => {
        console.error("Copy failed", err);
    });
}

function formatText(text) {
    if (!text) {
        return "";
    }

    let raw = String(text);

    // Strip reasoning / thinking tokens from deep-reasoning models
    raw = raw.replace(/<think>[\s\S]*?<\/think>/gi, "");
    raw = raw.replace(/<think>[\s\S]*/gi, "");

    // Extract fenced code blocks before HTML escaping
    const codeBlocks = [];
    raw = raw.replace(/```([a-zA-Z0-9_-]*)\r?\n([\s\S]*?)```/g, function(match, lang, code) {
        const placeholder = "___CODE_BLOCK_" + codeBlocks.length + "___";
        codeBlocks.push({ lang: lang || "code", code: code.trim() });
        return placeholder;
    });

    let formatted = escapeHTML(raw);
    formatted = formatted.replace(/\\n/g, "\n");

    // Inline code
    formatted = formatted.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

    // Pedagogical numbered sections: # 1. Intuition & Mental Model
    formatted = formatted.replace(/^#\s+(\d+)\.\s+(.*?)$/gm, '<div class="lesson-section-badge"><span class="section-num">$1</span><h2 class="lesson-section-title">$2</h2></div>');

    // Standard headings
    formatted = formatted.replace(/^#### (.*)$/gm, '<h4 class="lesson-subheading">$1</h4>');
    formatted = formatted.replace(/^### (.*)$/gm, '<h3 class="lesson-heading">$1</h3>');
    formatted = formatted.replace(/^## (.*)$/gm, '<h2 class="lesson-heading">$1</h2>');
    formatted = formatted.replace(/^# (.*)$/gm, '<h1 class="lesson-title">$1</h1>');

    // Callout boxes from blockquotes (e.g. > [!NOTE], > [!WARNING], > 💡, etc.)
    formatted = formatted.replace(
        /(?:^|\n)&gt;\s*\[!(?:NOTE|INFO)\]\s*(.*?)(?=(?:\n\n|\n(?!&gt;)|$))/gis,
        '<div class="callout callout-intuition"><div class="callout-icon">💡</div><div class="callout-body">$1</div></div>'
    );
    formatted = formatted.replace(
        /(?:^|\n)&gt;\s*\[!(?:WARNING|CAUTION)\]\s*(.*?)(?=(?:\n\n|\n(?!&gt;)|$))/gis,
        '<div class="callout callout-warning"><div class="callout-icon">⚠️</div><div class="callout-body">$1</div></div>'
    );
    formatted = formatted.replace(
        /(?:^|\n)&gt;\s*\[!(?:TIP|EXAMPLE)\]\s*(.*?)(?=(?:\n\n|\n(?!&gt;)|$))/gis,
        '<div class="callout callout-example"><div class="callout-icon">📝</div><div class="callout-body">$1</div></div>'
    );

    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Italic
    formatted = formatted.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");

    // Bullet points
    formatted = formatted.replace(/^\s*[-*]\s+(.*)$/gm, "<li>$1</li>");

    // Numbered lists
    formatted = formatted.replace(/^\s*(\d+)\.\s+(.*)$/gm, "<li>$2</li>");

    // Consecutive list items to ul
    formatted = formatted.replace(/(<li>.*?<\/li>\s*)+/gs, function(match) {
        return "<ul class=\"lesson-list\">" + match + "</ul>";
    });

    // Paragraph breaks
    formatted = formatted.replace(/\n{2,}/g, "</p><p>");
    formatted = formatted.replace(/\n/g, "<br>");

    // Re-insert styled code blocks with copy button
    codeBlocks.forEach(function(item, idx) {
        const placeholder = "___CODE_BLOCK_" + idx + "___";
        const codeHtml =
            '<pre class="code-block">' +
            '<div class="code-header"><span>' + escapeHTML(item.lang) + '</span><button class="copy-code-btn" onclick="copyCode(this)">Copy</button></div>' +
            '<code>' + escapeHTML(item.code) + '</code>' +
            '</pre>';
        formatted = formatted.replace(placeholder, codeHtml);
    });

    return "<div class='lesson-text'><p>" + formatted + "</p></div>";
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(text) {

    if (
        text === null ||
        text === undefined
    ) {

        return "";

    }


    return String(text)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// ============================================================
// PROGRESS
// ============================================================

// ============================================================
// PROGRESS
// ============================================================


// ------------------------------------------------------------
// LOAD SAVED PROGRESS
// ------------------------------------------------------------

function loadProgress() {

    try {

        const saved =
            localStorage.getItem(
                "arcLearnsProgress"
            );


        if (!saved) {
            return;
        }


        const data =
            JSON.parse(saved);


        topicsLearned =
            Number(
                data.topicsLearned || 0
            );


        quizzesTaken =
            Number(
                data.quizzesTaken || 0
            );


        totalQuizScore =
            Number(
                data.totalQuizScore || 0
            );

    }

    catch (error) {

        console.error(
            "PROGRESS LOAD ERROR:",
            error
        );

    }

}


// ------------------------------------------------------------
// SAVE PROGRESS
// ------------------------------------------------------------

function saveProgress() {

    try {

        localStorage.setItem(

            "arcLearnsProgress",

            JSON.stringify({

                topicsLearned:
                    topicsLearned,

                quizzesTaken:
                    quizzesTaken,

                totalQuizScore:
                    totalQuizScore

            })

        );

    }

    catch (error) {

        console.error(
            "PROGRESS SAVE ERROR:",
            error
        );

    }

}


// ------------------------------------------------------------
// GET QUIZ AVERAGE
// ------------------------------------------------------------

function getQuizAverage() {

    if (quizzesTaken <= 0) {

        return 0;

    }


    return Math.round(

        totalQuizScore /
        quizzesTaken

    );

}


// ------------------------------------------------------------
// UPDATE PROGRESS
// ------------------------------------------------------------

function updateProgress() {

    const progressPercent =
        document.getElementById(
            "progressPercent"
        );


    const progressFill =
        document.getElementById(
            "progressFill"
        );


    const topicsElement =
        document.getElementById(
            "topicsLearned"
        );


    const quizzesElement =
        document.getElementById(
            "quizzesTaken"
        );


    const quizScoreElement =
        document.getElementById(
            "quizScore"
        );


    const largeProgressFill =
        document.getElementById(
            "largeProgressFill"
        );


    const largeProgressPercent =
        document.getElementById(
            "largeProgressPercent"
        );


    // Calculate overall progress
    let progress =
        (topicsLearned * 10) +
        (quizzesTaken * 5);


    if (progress > 100) {

        progress = 100;

    }


    progress =
        Math.round(progress);


    // Dashboard progress
    if (progressPercent) {

        progressPercent.textContent =
            progress + "%";

    }


    if (progressFill) {

        progressFill.style.width =
            progress + "%";

    }


    // Large progress
    if (largeProgressPercent) {

        largeProgressPercent.textContent =
            progress + "%";

    }


    if (largeProgressFill) {

        largeProgressFill.style.width =
            progress + "%";

    }


    // Topics
    if (topicsElement) {

        topicsElement.textContent =
            topicsLearned;

    }


    // Quizzes
    if (quizzesElement) {

        quizzesElement.textContent =
            quizzesTaken;

    }


    // Quiz average
    if (quizScoreElement) {

        quizScoreElement.textContent =
            getQuizAverage() + "%";

    }


    // Save
    saveProgress();

}


// ------------------------------------------------------------
// RESET PROGRESS
// ------------------------------------------------------------

function resetProgress() {

    topicsLearned = 0;

    quizzesTaken = 0;

    totalQuizScore = 0;


    localStorage.removeItem(
        "arcLearnsProgress"
    );


    updateProgress();

}


// ============================================================
// BACKEND CONNECTION TEST
// ============================================================

async function checkBackend() {

    try {

        const response =
            await fetch(
                API_BASE + "/"
            );


        if (!response.ok) {

            throw new Error(
                "Backend unavailable"
            );

        }


        clearNotice();
        const data =
            await response.json();


        console.log(
            "ARC LEARNS BACKEND:",
            data.message
        );


    } catch (error) {

        console.error(
            "ARC LEARNS BACKEND ERROR:",
            error
        );

    }

}


// ============================================================
// OPTIONAL PHASE 12 TEACHING LENGTH SUPPORT
// ============================================================

function getTeachingLength() {

    const selectors = [

        "teachLength",

        "teachingLength",

        "lessonLength"

    ];


    for (
        let i = 0;
        i < selectors.length;
        i++
    ) {

        const element =
            document.getElementById(
                selectors[i]
            );


        if (element) {

            return element.value;

        }

    }


    return "medium";

}


// ============================================================
// OPTIONAL PHASE 12 ARC 0 SUPPORT
// ============================================================
//
// This function is prepared for the ARC 0 backend endpoint.
// It will work only after the backend provides:
//
// POST /arc0
//
// with:
//
// {
//     "question": "..."
// }
//
// ============================================================

async function sendARC0(question) {

    if (!question || !question.trim()) {

        return;

    }


    try {

        const response =
            await fetch(

                API_BASE + "/arc0",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        question:
                            question.trim()

                    })

                }

            );


        if (!response.ok) {

            throw await createAPIError(

                response,

                "ARC 0 is currently unavailable."

            );

        }


        return await response.json();


    } catch (error) {

        console.error(
            "ARC 0 ERROR:",
            error
        );


        throw error;

    }

}


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(

    "DOMContentLoaded",

    function() {

        updatePageTitle("landing");
        showSection("landing");
        

        loadProgress();

        updateProgress();


        checkBackend();


        // Allow file input to display supported types.

        const fileInput =
            document.getElementById(
                "pdfFile"
            );


        if (fileInput) {

            fileInput.setAttribute(

                "accept",

                ".pdf,.docx,.txt,.csv"

            );

        }

    }

);



function handleARC0Key(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendARC0FromUI();

    }

}


async function sendARC0FromUI() {
    const inputDirect = document.getElementById("arc0QuestionDirect");
    const inputStudio = document.getElementById("arc0Question");
    const msgDirect = document.getElementById("arc0MessagesDirect");
    const msgStudio = document.getElementById("arc0Messages");

    const question = (
        (inputDirect && inputDirect.value.trim()) ||
        (inputStudio && inputStudio.value.trim()) ||
        ""
    ).trim();

    if (!question) return;
    if (isARC0Busy) return;

    if (inputDirect) inputDirect.value = "";
    if (inputStudio) inputStudio.value = "";

    const containers = [msgDirect, msgStudio].filter(Boolean);
    containers.forEach(container => {
        const userDiv = document.createElement("div");
        userDiv.className = "message user-message";
        userDiv.innerHTML = `
            <div class="message-content">
                <strong>You</strong>
                <p>${escapeHTML(question)}</p>
            </div>
        `;
        container.appendChild(userDiv);
        container.scrollTop = container.scrollHeight;
    });

    const aiBubbles = [];
    containers.forEach(container => {
        const aiDiv = document.createElement("div");
        aiDiv.className = "message ai-message";
        aiDiv.innerHTML = `
            <div class="message-avatar">0</div>
            <div class="message-content">
                <strong>ARC Zero</strong>
                <p class="streaming-text"><span class="loading-pulse">Thinking...</span></p>
            </div>
        `;
        container.appendChild(aiDiv);
        container.scrollTop = container.scrollHeight;
        aiBubbles.push(aiDiv);
    });

    isARC0Busy = true;
    const clearNotice = withColdStartNotice("ARC Zero");

    try {
        let answer = "";
        let streamWorked = false;

        try {
            const response = await fetch(API_BASE + "/arc0/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    history: arc0History.slice(-6)
                })
            });

            if (response.ok && response.body) {
                clearNotice();
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    answer += chunk;
                    streamWorked = true;
                    aiBubbles.forEach(aiDiv => {
                        const contentEl = aiDiv.querySelector(".message-content");
                        if (contentEl) {
                            contentEl.innerHTML = `<strong>ARC Zero</strong>${formatText(answer)}`;
                        }
                    });
                    containers.forEach(c => c.scrollTop = c.scrollHeight);
                }
            }
        } catch (streamErr) {
            console.warn("ARC0 Stream error, falling back to sync endpoint:", streamErr);
        }

        if (!streamWorked || !answer.trim()) {
            const syncRes = await fetch(API_BASE + "/arc0", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    history: arc0History.slice(-6)
                })
            });
            clearNotice();
            if (!syncRes.ok) throw await createAPIError(syncRes, "ARC Zero is currently unavailable.");
            const syncData = await syncRes.json();
            answer = syncData.answer || syncData.response || "";
        }

        if (!answer.trim()) throw new Error("ARC Zero returned an empty response.");

        aiBubbles.forEach(aiDiv => {
            const contentEl = aiDiv.querySelector(".message-content");
            if (contentEl) {
                contentEl.innerHTML = `<strong>ARC Zero</strong>${formatText(answer)}`;
            }
        });
        containers.forEach(c => c.scrollTop = c.scrollHeight);

        arc0History.push({ role: "user", content: question });
        arc0History.push({ role: "assistant", content: answer });

    } catch (err) {
        clearNotice();
        console.error("ARC0 Error:", err);
        aiBubbles.forEach(aiDiv => {
            const contentEl = aiDiv.querySelector(".message-content");
            if (contentEl) {
                contentEl.innerHTML = `<strong>ARC Zero</strong><p class="error-msg">⚠️ ${escapeHTML(err.message || "Failed to reach AI service.")}</p>`;
            }
        });
        showToast(err.message || "ARC Zero error", "error");
    } finally {
        isARC0Busy = false;
    }
}

// ============================================================
// DIRECT SECTION BRIDGES & QUICK LAUNCHERS
// ============================================================

function teachTopicDirect() {
    teachTopic();
}

function sendChatDirect() {
    sendChat();
}

function handleChatKeyDirect(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChat();
    }
}

function sendARC0Direct() {
    sendARC0FromUI();
}

function handleARC0KeyDirect(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendARC0FromUI();
    }
}

function generateQuizDirect() {
    generateQuiz();
}

function quickFillARC0(promptText) {
    const d = document.getElementById("arc0QuestionDirect");
    const s = document.getElementById("arc0Question");
    if (d) d.value = promptText;
    if (s) s.value = promptText;
    sendARC0FromUI();
}

function quickFillChat(promptText) {
    const d = document.getElementById("chatQuestionDirect");
    const s = document.getElementById("chatQuestion");
    if (d) d.value = promptText;
    if (s) s.value = promptText;
    sendChat();
}

function quickFillTeach(topic) {
    const dTopic = document.getElementById("teachTopicDirect");
    const sTopic = document.getElementById("teachTopic");
    if (dTopic) dTopic.value = topic;
    if (sTopic) sTopic.value = topic;
    teachTopic();
}

function quickFillQuiz(topic) {
    const dTopic = document.getElementById("quizTopicDirect");
    const sTopic = document.getElementById("quizTopic");
    if (dTopic) dTopic.value = topic;
    if (sTopic) sTopic.value = topic;
    generateQuiz();
}

function copyLessonText(btn) {
    const card = btn.closest(".lesson-content");
    if (!card) return;
    const text = card.innerText.replace("📋 Copy Lesson", "").trim();
    navigator.clipboard.writeText(text).then(() => {
        const orig = btn.innerText;
        btn.innerText = "✓ Copied!";
        setTimeout(() => btn.innerText = orig, 2000);
        showToast("Lesson copied to clipboard!", "success");
    });
}

// ============================================================
// LIVE PROVIDER STATUS FETCH
// ============================================================

async function fetchProviderStatus() {
    try {
        const res = await fetch(API_BASE + "/status");
        if (!res.ok) return;
        const data = await res.json();
        const providers = data.providers || {};
        const primary = providers.active_primary || "gemini";

        const hudPrimary = document.getElementById("hudPrimaryProvider");
        const sidebarStatus = document.getElementById("sidebarEngineStatus");
        const speedDisplay = document.getElementById("speedDisplay");
        const sidebarSpeed = document.getElementById("sidebarEngineSpeed");

        if (primary === "gemini") {
            if (hudPrimary) hudPrimary.textContent = "Google Gemini 3 Flash";
            if (sidebarStatus) sidebarStatus.textContent = "Google Gemini Active";
            if (speedDisplay) speedDisplay.textContent = "Speed: ~0.3s (Sub-Second)";
            if (sidebarSpeed) sidebarSpeed.textContent = "Latency: < 0.3s • 1,500/day Free";
        } else if (primary === "groq") {
            if (hudPrimary) hudPrimary.textContent = "Groq LPU (500 tok/s)";
            if (sidebarStatus) sidebarStatus.textContent = "Groq LPU Active";
            if (speedDisplay) speedDisplay.textContent = "Speed: ~0.2s (Instant)";
            if (sidebarSpeed) sidebarSpeed.textContent = "Latency: < 0.2s • Ultra-Fast";
        } else if (primary === "openrouter") {
            if (hudPrimary) hudPrimary.textContent = "OpenRouter Multi-Model";
            if (sidebarStatus) sidebarStatus.textContent = "OpenRouter Active";
        }
    } catch (e) {
        console.debug("Could not fetch provider status:", e);
    }
}

// ============================================================
// CYBERNETIC NEURAL CANVAS ANIMATION
// ============================================================

function initCyberCanvas() {
    const canvas = document.getElementById("cyberCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const count = Math.min(60, Math.floor((width * height) / 25000));

    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 1.8 + 1,
            color: Math.random() > 0.4 ? "rgba(0, 245, 255, " : "rgba(168, 85, 247, ",
            alpha: Math.random() * 0.5 + 0.25
        });
    }

    function render() {
        ctx.clearRect(0, 0, width, height);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 130) {
                    const lineAlpha = (1 - dist / 130) * 0.2;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(0, 245, 255, ${lineAlpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw particles
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ")";
            ctx.shadowColor = p.color + "0.8)";
            ctx.shadowBlur = 6;
            ctx.fill();
        }

        requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
}

// ============================================================
// DIRECT SECTION EVENT ATTACHMENTS & GLOBAL EXPORTS
// ============================================================

function attachDirectActionListeners() {
    // 1. ARC Zero
    const arc0Btn = document.getElementById("arc0SendBtnDirect");
    if (arc0Btn) arc0Btn.onclick = (e) => { e.preventDefault(); sendARC0FromUI(); };
    const arc0In = document.getElementById("arc0QuestionDirect");
    if (arc0In) {
        arc0In.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendARC0FromUI();
            }
        };
    }

    // 2. Ask AI
    const chatBtn = document.getElementById("chatSendBtnDirect");
    if (chatBtn) chatBtn.onclick = (e) => { e.preventDefault(); sendChat(); };
    const chatIn = document.getElementById("chatQuestionDirect");
    if (chatIn) {
        chatIn.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendChat();
            }
        };
    }

    // 3. AI Teacher
    const teachBtn = document.getElementById("teachBtnDirect");
    if (teachBtn) teachBtn.onclick = (e) => { e.preventDefault(); teachTopic(); };
    const teachIn = document.getElementById("teachTopicDirect");
    if (teachIn) {
        teachIn.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                teachTopic();
            }
        };
    }

    // 4. Turbo Quiz
    const quizBtn = document.getElementById("quizBtnDirect");
    if (quizBtn) quizBtn.onclick = (e) => { e.preventDefault(); generateQuiz(); };
    const quizIn = document.getElementById("quizTopicDirect");
    if (quizIn) {
        quizIn.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                generateQuiz();
            }
        };
    }
}

// Expose all UI entrypoints globally on window
window.sendARC0FromUI = sendARC0FromUI;
window.sendARC0Direct = sendARC0Direct;
window.handleARC0KeyDirect = handleARC0KeyDirect;
window.sendChat = sendChat;
window.sendChatDirect = sendChatDirect;
window.handleChatKeyDirect = handleChatKeyDirect;
window.teachTopic = teachTopic;
window.teachTopicDirect = teachTopicDirect;
window.generateQuiz = generateQuiz;
window.generateQuizDirect = generateQuizDirect;
window.quickFillARC0 = quickFillARC0;
window.quickFillChat = quickFillChat;
window.quickFillTeach = quickFillTeach;
window.quickFillQuiz = quickFillQuiz;
window.copyLessonText = copyLessonText;
window.showSection = showSection;

// Auto-run on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        initCyberCanvas();
        fetchProviderStatus();
        attachDirectActionListeners();
    });
} else {
    initCyberCanvas();
    fetchProviderStatus();
    attachDirectActionListeners();
}

