document.addEventListener("DOMContentLoaded", function () {

    // =========================================
    // ELEMENTS
    // =========================================

    const quizForm = document.getElementById("quizForm");

    const quizTitle = document.getElementById("quizTitle");
    const gameMode = document.getElementById("gameMode");

    const questionType = document.getElementById("questionType");
    const questionText = document.getElementById("questionText");

    const optionA = document.getElementById("optionA");
    const optionB = document.getElementById("optionB");
    const optionC = document.getElementById("optionC");
    const optionD = document.getElementById("optionD");

    const correctAnswer = document.getElementById("correctAnswer");
    const timer = document.getElementById("timer");

    const addQuestionBtn = document.getElementById("addQuestionBtn");

    const questionNumber = document.getElementById("questionNumber");

    const questionsListSection =
        document.getElementById("questionsListSection");

    const questionsList =
        document.getElementById("questionsList");

    const totalQuestions =
        document.getElementById("totalQuestions");

    const createQuizBtn =
        document.getElementById("createQuizBtn");


    // =========================================
    // QUESTIONS ARRAY
    // =========================================

    let questions = [];



    // =========================================
    // QUESTION TYPE CHANGE
    // =========================================

    questionType.addEventListener("change", function () {

        const type = questionType.value;

        const multipleChoiceSection =
            document.getElementById("multipleChoiceSection");


        if (type === "multiple_choice") {

            multipleChoiceSection.style.display = "block";

            optionA.disabled = false;
            optionB.disabled = false;
            optionC.disabled = false;
            optionD.disabled = false;

        } else {

            multipleChoiceSection.style.display = "none";

            optionA.value = "";
            optionB.value = "";
            optionC.value = "";
            optionD.value = "";

        }


        // =====================================
        // TRUE / FALSE
        // =====================================

        if (type === "true_false") {

            correctAnswer.placeholder =
                "Enter True or False";

        }

        // =====================================
        // JUMBLED
        // =====================================

        else if (type === "jumbled") {

            correctAnswer.placeholder =
                "Enter the correct word";

        }

        // =====================================
        // TYPE ANSWER
        // =====================================

        else if (type === "type_answer") {

            correctAnswer.placeholder =
                "Enter the correct answer";

        }

        // =====================================
        // MULTIPLE CHOICE
        // =====================================

        else {

            correctAnswer.placeholder =
                "Example: A";

        }

    });



    // =========================================
    // VALIDATE QUESTION
    // =========================================

    function validateQuestion() {

        const text =
            questionText.value.trim();

        const answer =
            correctAnswer.value.trim();


        if (!text) {

            alert("Please enter your question.");

            questionText.focus();

            return false;
        }


        if (!answer) {

            alert("Please enter the correct answer.");

            correctAnswer.focus();

            return false;
        }


        // =====================================
        // MULTIPLE CHOICE VALIDATION
        // =====================================

        if (questionType.value === "multiple_choice") {

            if (!optionA.value.trim()) {

                alert("Please enter Choice A.");

                optionA.focus();

                return false;
            }


            if (!optionB.value.trim()) {

                alert("Please enter Choice B.");

                optionB.focus();

                return false;
            }


            if (!optionC.value.trim()) {

                alert("Please enter Choice C.");

                optionC.focus();

                return false;
            }


            if (!optionD.value.trim()) {

                alert("Please enter Choice D.");

                optionD.focus();

                return false;
            }


            const correct =
                answer.toUpperCase();


            if (
                correct !== "A" &&
                correct !== "B" &&
                correct !== "C" &&
                correct !== "D"
            ) {

                alert(
                    "For Multiple Choice, Correct Answer must be A, B, C, or D."
                );

                correctAnswer.focus();

                return false;
            }

        }



        // =====================================
        // TRUE / FALSE VALIDATION
        // =====================================

        if (questionType.value === "true_false") {

            const answerLower =
                answer.toLowerCase();


            if (
                answerLower !== "true" &&
                answerLower !== "false"
            ) {

                alert(
                    "For True or False, the correct answer must be True or False."
                );

                correctAnswer.focus();

                return false;
            }

        }


        return true;

    }



    // =========================================
    // GET CURRENT QUESTION
    // =========================================

    function getCurrentQuestion() {

        return {

            question_type:
                questionType.value,

            question_text:
                questionText.value.trim(),

            option_a:
                optionA.value.trim(),

            option_b:
                optionB.value.trim(),

            option_c:
                optionC.value.trim(),

            option_d:
                optionD.value.trim(),

            correct_answer:
                correctAnswer.value.trim(),

            timer:
                parseInt(timer.value) || 0

        };

    }



    // =========================================
    // CLEAR QUESTION FORM
    // =========================================

    function clearQuestionForm() {

        questionText.value = "";

        optionA.value = "";
        optionB.value = "";
        optionC.value = "";
        optionD.value = "";

        correctAnswer.value = "";

        timer.value = "30";

        questionType.value =
            "multiple_choice";


        document.getElementById(
            "multipleChoiceSection"
        ).style.display = "block";


        updateQuestionNumber();

        questionText.focus();

    }



    // =========================================
    // UPDATE QUESTION NUMBER
    // =========================================

    function updateQuestionNumber() {

        questionNumber.textContent =
            "Question " + (questions.length + 1);

    }



    // =========================================
    // DISPLAY QUESTIONS
    // =========================================

    function renderQuestions() {

        questionsList.innerHTML = "";


        if (questions.length === 0) {

            questionsListSection.style.display =
                "none";

            totalQuestions.textContent =
                "0 Questions";

            return;

        }


        questionsListSection.style.display =
            "block";


        totalQuestions.textContent =
            questions.length +
            (questions.length === 1
                ? " Question"
                : " Questions");


        questions.forEach(function (question, index) {

            const card =
                document.createElement("div");


            card.className =
                "added-question";


            let typeName = "";


            if (
                question.question_type ===
                "multiple_choice"
            ) {

                typeName = "Multiple Choice";

            } else if (
                question.question_type ===
                "true_false"
            ) {

                typeName = "True or False";

            } else if (
                question.question_type ===
                "jumbled"
            ) {

                typeName = "Jumbled Words";

            } else {

                typeName = "Type Answer";

            }


            card.innerHTML = `

                <div class="added-question-header">

                    <strong>
                        Question ${index + 1}
                    </strong>

                    <button
                        type="button"
                        class="remove-question-btn"
                        data-index="${index}"
                    >
                        Remove
                    </button>

                </div>


                <p class="question-preview">
                    ${escapeHtml(question.question_text)}
                </p>


                <div class="question-meta">

                    <span>
                        ${typeName}
                    </span>

                    <span>
                        ${question.timer === 0
                            ? "No Timer"
                            : question.timer + " seconds"}
                    </span>

                </div>

            `;


            questionsList.appendChild(card);

        });


        // =====================================
        // REMOVE QUESTION BUTTONS
        // =====================================

        document
            .querySelectorAll(".remove-question-btn")
            .forEach(function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        const index =
                            parseInt(
                                button.dataset.index
                            );


                        questions.splice(
                            index,
                            1
                        );


                        renderQuestions();

                        updateQuestionNumber();

                    }
                );

            });

    }



    // =========================================
    // ESCAPE HTML
    // =========================================

    function escapeHtml(text) {

        const div =
            document.createElement("div");

        div.textContent = text;

        return div.innerHTML;

    }



    // =========================================
    // ADD QUESTION
    // =========================================

    addQuestionBtn.addEventListener(
        "click",
        function () {

            // Validate current question

            if (!validateQuestion()) {

                return;

            }


            // Get question

            const newQuestion =
                getCurrentQuestion();


            // Add to array

            questions.push(
                newQuestion
            );


            // Update UI

            renderQuestions();


            // Clear form

            clearQuestionForm();


            // Show confirmation

            alert(
                "Question " +
                questions.length +
                " added successfully!"
            );

        }
    );



    // =========================================
    // CREATE QUIZ
    // =========================================

    quizForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            // =====================================
            // QUIZ TITLE
            // =====================================

            const title =
                quizTitle.value.trim();


            if (!title) {

                alert(
                    "Please enter a quiz title."
                );

                quizTitle.focus();

                return;

            }



            // =====================================
            // SAVE CURRENT QUESTION AUTOMATICALLY
            // =====================================

            const currentText =
                questionText.value.trim();


            const currentAnswer =
                correctAnswer.value.trim();


            if (
                currentText !== "" ||
                currentAnswer !== ""
            ) {

                if (!validateQuestion()) {

                    return;

                }


                questions.push(
                    getCurrentQuestion()
                );

            }



            // =====================================
            // CHECK QUESTIONS
            // =====================================

            if (questions.length === 0) {

                alert(
                    "Please add at least one question before creating the quiz."
                );

                return;

            }



            // =====================================
            // DISABLE BUTTON
            // =====================================

            createQuizBtn.disabled = true;

            createQuizBtn.textContent =
                "Creating Quiz...";



            // =====================================
            // DATA TO FLASK
            // =====================================

            const quizData = {

                title: title,

                game_mode:
                    gameMode.value,

                questions:
                    questions

            };



            try {

                const response =
                    await fetch(
                        "/api/create-quiz",
                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify(
                                    quizData
                                )

                        }
                    );


                const result =
                    await response.json();



                // =================================
                // SUCCESS
                // =================================

                if (response.ok) {

                    alert(
                        "Quiz created successfully!"
                    );


                    // Redirect

                    window.location.href =
                        "/dashboard";

                }

                // =================================
                // ERROR
                // =================================

                else {

                    alert(
                        result.error ||
                        "Failed to create quiz."
                    );

                }

            }


            catch (error) {

                console.error(error);

                alert(
                    "Something went wrong while creating the quiz."
                );

            }


            finally {

                createQuizBtn.disabled =
                    false;

                createQuizBtn.textContent =
                    "Create Quiz";

            }

        }
    );



    // =========================================
    // INITIAL STATE
    // =========================================

    updateQuestionNumber();

});
