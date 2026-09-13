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

    const topicInput =
        document.getElementById("teachTopic");


    const output =
        document.getElementById("lessonOutput");


    if (!topicInput || !output) {

        return;

    }


    const topic =
        topicInput.value.trim();
    const outputDirect = document.getElementById("lessonOutputDirect");


    if (!topic) {

        output.innerHTML =

            '<div class="empty-state">' +

            '<div>⚠️</div>' +

            '<h3>Please enter a topic</h3>' +

            '<p>' +
            'Enter a topic from your uploaded study material.' +
            '</p>' +

            '</div>';

        return;

    }


    if (isTeaching) {

        return;

    }


    isTeaching = true;


    // ========================================================
    // Get selected teaching length
    // ========================================================

    const length =
        getTeachingLength();


    // ========================================================
    // Initial loading message
    // ========================================================

    output.innerHTML =

        '<div class="lesson-content">' +

        '<h2>' +
        escapeHTML(topic) +
        '</h2>' +

        '<p>' +
        '🧠 ARC AI is starting your lesson...' +
        '</p>' +

        '</div>';


    const clearNotice = withColdStartNotice("Lesson");
    try {
        const response =
            await fetch(
                API_BASE + "/teach/stream",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        topic: topic,

                        length: length

                    })

                }

            );


        if (!response.ok) {

            throw await createAPIError(

                response,

                "Unable to generate lesson."

            );

        }


        // ====================================================
        // Make sure streaming is supported
        // ====================================================

        if (!response.body) {

            throw new Error(
                "Streaming is not supported by this browser."
            );

        }


        // ====================================================
        // Prepare reader
        // ====================================================

        clearNotice();
        clearNotice();
        const reader =
            response.body.getReader();


        const decoder =
            new TextDecoder();


        let lessonText = "";


        // ====================================================
        // Read streaming response
        // ====================================================

        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {

                break;

            }


            const chunk =
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            lessonText += chunk;


            // =================================================
            // Update lesson immediately
            // =================================================

            const renderedHtml =
                '<div class="lesson-content">' +
                '<h2>' + escapeHTML(topic) + '</h2>' +
                formatText(lessonText) +
                '</div>';
            output.innerHTML = renderedHtml;
            output.scrollTop = output.scrollHeight;
            if (outputDirect) {
                outputDirect.innerHTML = renderedHtml;
                outputDirect.scrollTop = outputDirect.scrollHeight;
            }

        }


        // ====================================================
        // Final rendering
        // ====================================================

        if (!lessonText.trim()) {

            throw new Error(
                "ARC AI returned an empty lesson."
            );

        }


        output.innerHTML =

            '<div class="lesson-content">' +

            '<h2>' +
            escapeHTML(topic) +
            '</h2>' +

            formatText(
                lessonText
            ) +

            '</div>';


        topicsLearned++;


        updateProgress();


    } catch (error) {
        clearNotice();
        console.error(
            "TEACH STREAM ERROR:",
            error
        );


        output.innerHTML =

            '<div class="empty-state">' +

            '<div>⚠️</div>' +

            '<h3>Unable to generate lesson</h3>' +

            '<p>' +
            escapeHTML(
                error.message ||
                "Something went wrong."
            ) +
            '</p>' +

            '</div>';


    } finally {

        isTeaching = false;

    }

}

// ============================================================
// ASK ARC AI / CHAT
// ============================================================

async function sendChat() {

    const input =
        document.getElementById(
            "chatQuestion"
        );


    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (!input || !messages) {

        return;

    }


    const question =
        input.value.trim();


    if (!question) {

        return;

    }


    if (isChatting) {

        return;

    }


    // ========================================================
    // Add user's message
    // ========================================================

    addChatMessage(
        "user",
        escapeHTML(question)
    );


    input.value = "";


    // ========================================================
    // Add temporary AI message
    // ========================================================

    const loadingId =
        addChatMessage(
            "ai",
            "ARC AI is starting..."
        );


    isChatting = true;


    const clearNotice = withColdStartNotice("Chat");
    try {
        const response =
            await fetch(
                API_BASE + "/chat/stream",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({
                        question: question,
                        history: chatHistory.slice(-6)
                    })

                }

            );


        if (!response.ok) {

            throw await createAPIError(
                response,
                "Unable to get an answer."
            );

        }


        // ====================================================
        // Make sure streaming is available
        // ====================================================

        if (!response.body) {

            throw new Error(
                "Streaming is not supported by this browser."
            );

        }


        // ====================================================
        // Get response reader
        // ====================================================

        clearNotice();
        clearNotice();
        const reader =
            response.body.getReader();


        const decoder =
            new TextDecoder();


        let answer = "";


        // ====================================================
        // Read chunks as they arrive
        // ====================================================

        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {

                break;

            }


            const chunk =
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            answer += chunk;


            // =================================================
            // Update the existing AI message
            // =================================================

            const messageElement =
                document.getElementById(
                    loadingId
                );


            if (messageElement) {

                const contentElement =
                    messageElement.querySelector(
                        ".message-content"
                    );


                if (contentElement) {

                    contentElement.innerHTML =
                        formatText(answer);

                }

            }


            // Keep latest answer visible
            messages.scrollTop =
                messages.scrollHeight;

        }


        // ====================================================
        // Final answer
        // ====================================================

        if (!answer.trim()) {

            throw new Error(
                "No answer was returned."
            );

        }


        const finalMessage =
            document.getElementById(
                loadingId
            );


        if (finalMessage) {

            const contentElement =
                finalMessage.querySelector(
                    ".message-content"
                );


            if (contentElement) {

                contentElement.innerHTML =
                    formatText(answer);

            }

        }

        chatHistory.push({ role: "user", content: question });
        chatHistory.push({ role: "assistant", content: answer });


    } catch (error) {
        clearNotice();
        console.error(
            "CHAT STREAM ERROR:",
            error
        );


        removeChatMessage(
            loadingId
        );


        addChatMessage(

            "ai",

            "Sorry, ARC AI could not answer your question." +

            "<br><br>" +

            escapeHTML(
                error.message ||
                "Something went wrong."
            )

        );


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

    const topicInput =
        document.getElementById(
            "quizTopic"
        );


    const output =
        document.getElementById(
            "quizOutput"
        );


    if (!topicInput || !output) {

        return;

    }


    const topic =
        topicInput.value.trim();
    const outputDirect = document.getElementById("lessonOutputDirect");


    if (!topic) {

        output.innerHTML =

            '<div class="empty-state">' +

            '<div>⚠️</div>' +

            '<h3>Please enter a topic</h3>' +

            '<p>' +
            'Enter a topic from your uploaded study material.' +
            '</p>' +

            '</div>';

        return;

    }


    if (isGeneratingQuiz) {

        return;

    }


    const questionCount =
        getQuizQuestionCount();


    isGeneratingQuiz = true;


    output.innerHTML =

        '<div class="empty-state">' +

        '<div>🎯</div>' +

        '<h3>Generating your quiz...</h3>' +

        '<p>' +

        "ARC AI is preparing " +

        questionCount +

        " questions." +

        '</p>' +

        '</div>';


    const clearNotice = withColdStartNotice("Quiz");
    try {
        const response =
            await fetch(
                API_BASE + "/quiz",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        topic: topic,

                        number_of_questions:
                            questionCount

                    })

                }
            );


        if (!response.ok) {

            throw await createAPIError(
                response,
                "Unable to generate quiz."
            );

        }


        clearNotice();
        clearNotice();
        const data =
            await response.json();

        if (
            !data.quiz ||
            data.quiz.length === 0
        ) {

            throw new Error(

                data.message ||

                data.error ||

                "No quiz questions were returned."

            );

        }


        currentQuizTotal =
            data.quiz.length;

        currentQuizAnswered = 0;

        currentQuizCorrect = 0;


        renderQuiz(
            data.quiz
        );


    } catch (error) {
        clearNotice();
        console.error(
            "QUIZ ERROR:",
            error
        );


        output.innerHTML =

            '<div class="empty-state">' +

            '<div>⚠️</div>' +

            '<h3>Unable to generate quiz</h3>' +

            '<p>' +
            escapeHTML(
                error.message
            ) +
            '</p>' +

            '</div>';


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

    const output =
        document.getElementById(
            "quizOutput"
        );


    if (!output) {

        return;

    }


    output.innerHTML = "";
    missedConcepts = [];

    const quizContainer = document.createElement("div");
    quizContainer.className = "quiz-container";

    quiz.forEach(function(item, questionIndex) {
        const card = document.createElement("div");
        card.className = "quiz-card";

        // Meta Header: Question #, Difficulty, Concept Tag
        const metaRow = document.createElement("div");
        metaRow.className = "quiz-meta-row";

        const number = document.createElement("span");
        number.className = "quiz-number";
        number.textContent = "Q" + (questionIndex + 1);

        const diffBadge = document.createElement("span");
        const diff = (item.difficulty || "medium").toLowerCase();
        diffBadge.className = "badge-difficulty " + diff;
        diffBadge.textContent = diff.toUpperCase();

        metaRow.appendChild(number);
        metaRow.appendChild(diffBadge);

        if (item.concept_tested) {
            const conceptBadge = document.createElement("span");
            conceptBadge.className = "badge-concept";
            conceptBadge.textContent = item.concept_tested;
            metaRow.appendChild(conceptBadge);
        }

        card.appendChild(metaRow);

        // Question Title
        const question = document.createElement("h3");
        question.className = "quiz-question";
        question.textContent = item.question || "Question";
        card.appendChild(question);

        // Options
        const options = Array.isArray(item.options) ? item.options : [];
        const optionsContainer = document.createElement("div");
        optionsContainer.className = "quiz-options";

        options.forEach(function(option) {
            const button = document.createElement("button");
            button.className = "quiz-option";
            button.textContent = option;

            button.onclick = function() {
                handleQuizAnswer(
                    button,
                    option,
                    item,
                    card
                );
            };

            optionsContainer.appendChild(button);
        });

        card.appendChild(optionsContainer);
        quizContainer.appendChild(card);
    });

    output.appendChild(quizContainer);
}


// ============================================================
// HANDLE QUIZ ANSWER (IMMEDIATE PEDAGOGICAL FEEDBACK)
// ============================================================

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

    const input =
        document.getElementById(
            "arc0Question"
        );


    const messages =
        document.getElementById(
            "arc0Messages"
        );


    if (!input || !messages) {

        return;

    }


    const question =
        input.value.trim();


    if (!question) {

        return;

    }


    // ========================================================
    // Display user's message
    // ========================================================

    const userMessage =
        document.createElement("div");


    userMessage.className =
        "message user-message";


    userMessage.innerHTML =

        '<div class="message-content">' +

        '<strong>You</strong>' +

        '<p>' +
        escapeHTML(question) +
        '</p>' +

        '</div>';


    messages.appendChild(
        userMessage
    );


    // ========================================================
    // Clear input
    // ========================================================

    input.value = "";


    messages.scrollTop =
        messages.scrollHeight;


    // ========================================================
    // Create ARC 0 AI message
    // ========================================================

    const aiMessage =
        document.createElement("div");


    aiMessage.className =
        "message ai-message";


    aiMessage.innerHTML =

        '<div class="message-avatar">' +
        'A' +
        '</div>' +

        '<div class="message-content">' +

        '<strong>ARC 0</strong>' +

        '<p>Thinking...</p>' +

        '</div>';


    messages.appendChild(
        aiMessage
    );


    messages.scrollTop =
        messages.scrollHeight;


    const clearNotice = withColdStartNotice("ARC 0");
    try {
        const response =
            await fetch(
                API_BASE + "/arc0/stream",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({
                        question: question,
                        history: arc0History.slice(-6)
                    })

                }

            );


        // ====================================================
        // Check response
        // ====================================================

        if (!response.ok) {

            throw await createAPIError(

                response,

                "ARC 0 is currently unavailable."

            );

        }


        // ====================================================
        // Check streaming support
        // ====================================================

        if (!response.body) {

            throw new Error(
                "Streaming is not supported by this browser."
            );

        }


        // ====================================================
        // Prepare stream reader
        // ====================================================

        clearNotice();
        clearNotice();
        const reader =
            response.body.getReader();


        const decoder =
            new TextDecoder();


        let answer = "";


        // ====================================================
        // Read response chunks
        // ====================================================

        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {

                break;

            }


            const chunk =
                decoder.decode(

                    value,

                    {
                        stream: true
                    }

                );


            answer += chunk;


            // =================================================
            // Update answer immediately
            // =================================================

            const contentElement =
                aiMessage.querySelector(
                    ".message-content"
                );


            if (contentElement) {

                contentElement.innerHTML =

                    '<strong>ARC 0</strong>' +

                    formatText(
                        answer
                    );

            }


            // Keep latest text visible
            messages.scrollTop =
                messages.scrollHeight;

        }


        // ====================================================
        // Final answer validation
        // ====================================================

        if (!answer.trim()) {

            throw new Error(
                "ARC 0 returned an empty answer."
            );

        }


        // ====================================================
        // Final rendering
        // ====================================================

        const finalContent =
            aiMessage.querySelector(
                ".message-content"
            );


        if (finalContent) {

            finalContent.innerHTML =

                '<strong>ARC 0</strong>' +

                formatText(
                    answer
                );

        }

        arc0History.push({ role: "user", content: question });
        arc0History.push({ role: "assistant", content: answer });


    } catch (error) {
        clearNotice();
        console.error(
            "ARC 0 STREAM ERROR:",
            error
        );


        aiMessage.innerHTML =

            '<div class="message-avatar">' +
            'A' +
            '</div>' +

            '<div class="message-content">' +

            '<strong>ARC 0</strong>' +

            '<p>⚠️ ' +

            escapeHTML(

                error.message ||

                "ARC 0 is currently unavailable."

            ) +

            '</p>' +

            '</div>';

    }


    messages.scrollTop =
        messages.scrollHeight;

}
// ============================================================
// DIRECT SECTION BRIDGES
// ============================================================

function teachTopicDirect() {
    const dTopic = document.getElementById("teachTopicDirect");
    const sTopic = document.getElementById("teachTopic");
    const dLen = document.getElementById("teachLengthDirect");
    const sLen = document.getElementById("teachLength");
    if (dTopic && sTopic) sTopic.value = dTopic.value;
    if (dLen && sLen) sLen.value = dLen.value;
    teachTopic(true);
}

function sendChatDirect() {
    const dInput = document.getElementById("chatQuestionDirect");
    const sInput = document.getElementById("chatQuestion");
    if (dInput && sInput) sInput.value = dInput.value;
    sendChat(true);
}

function handleChatKeyDirect(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChatDirect();
    }
}

function sendARC0Direct() {
    const dInput = document.getElementById("arc0QuestionDirect");
    const sInput = document.getElementById("arc0Question");
    if (dInput && sInput) sInput.value = dInput.value;
    sendARC0FromUI(true);
}

function handleARC0KeyDirect(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendARC0Direct();
    }
}

function generateQuizDirect() {
    const dTopic = document.getElementById("quizTopicDirect");
    const sTopic = document.getElementById("quizTopic");
    const dCount = document.getElementById("quizCountDirect");
    const sCount = document.getElementById("quizQuestionCount");
    if (dTopic && sTopic) sTopic.value = dTopic.value;
    if (dCount && sCount) sCount.value = dCount.value;
    generateQuiz(true);
}
