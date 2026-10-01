console.log("QuizUp JavaScript loaded!");


// =====================================
// ANIMAL SELECTION
// =====================================

const animals = document.querySelectorAll(".animal");

animals.forEach(function(animal) {

    animal.addEventListener("click", function() {

        animals.forEach(function(item) {

            item.classList.remove("selected");

        });

        animal.classList.add("selected");

    });

});


// =====================================
// JOIN GAME
// =====================================

const joinForm = document.getElementById("joinForm");

if (joinForm) {

    joinForm.addEventListener("submit", function(event) {

        event.preventDefault();

        const code =
            document.getElementById("gameCode").value;

        const name =
            document.getElementById("playerName").value;


        if (code.length !== 6) {

            alert("Please enter a valid 6-character game code.");

            return;

        }


        if (name.trim() === "") {

            alert("Please enter your name.");

            return;

        }


        window.location.href = "/play";

    });

}


// =====================================
// CREATE QUIZ
// =====================================

const quizForm = document.getElementById("quizForm");

if (quizForm) {

    quizForm.addEventListener("submit", function(event) {

        event.preventDefault();


        const title =
            document.getElementById("quizTitle").value;


        if (title.trim() === "") {

            alert("Please enter a quiz title.");

            return;

        }


        alert(
            "Quiz created successfully!\n\n" +
            "Database connection will be added next."
        );


        window.location.href = "/dashboard";

    });

}


// =====================================
// QUESTION TYPE
// =====================================

const questionType =
    document.getElementById("questionType");


const multipleChoiceSection =
    document.getElementById("multipleChoiceSection");


if (questionType && multipleChoiceSection) {

    questionType.addEventListener("change", function() {

        if (this.value === "multiple_choice") {

            multipleChoiceSection.style.display = "block";

        } else {

            multipleChoiceSection.style.display = "none";

        }

    });

}


// =====================================
// ADD QUESTION
// =====================================

let questionCount = 1;


function addQuestion() {

    questionCount++;


    const questionNumber =
        document.getElementById("questionNumber");


    if (questionNumber) {

        questionNumber.textContent =
            "Question " + questionCount;

    }


    const questionText =
        document.getElementById("questionText");


    if (questionText) {

        questionText.value = "";

    }


    const correctAnswer =
        document.getElementById("correctAnswer");


    if (correctAnswer) {

        correctAnswer.value = "";

    }


    alert(
        "New question started!\n\n" +
        "Question " + questionCount
    );

}


// =====================================
// COMING SOON
// =====================================

function showComingSoon() {

    alert(
        "Reports & Analytics\n\n" +
        "This feature will be connected to Supabase next."
    );

}


// =====================================
// PLAY QUIZ
// =====================================

const choices =
    document.querySelectorAll(".choice");


choices.forEach(function(choice) {

    choice.addEventListener("click", function() {


        choices.forEach(function(item) {

            item.classList.remove("selected");

        });


        choice.classList.add("selected");


        setTimeout(function() {

            alert(
                "Answer submitted!\n\n" +
                "Real-time scoring will be connected to Supabase next."
            );

        }, 300);

    });

});