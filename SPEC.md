I would like to build a command-line Python quiz app with a local login system that reads questions from a JSON file, quizzes users, tracks scores and performance statistics securely (in a non-human-readable format), allows users to provide feedback on questions to influence future quiz selections, and saves results.

Behavior: Here is what the app should do, step by step, from the user's perspective:

1. Greet the user with a friendly message.
2. Ask the user how many questions they would like, the difficulty of questions they would like, and any filter(s) they would like to apply to the questions (by category of question).
3. Randomly select the desired number of questions from the question bank.
4. Show the user the question and have them input the answer they think it is.
5. Display a corresponding message whether they got the correct answer or not and their current score, should also give the user the option to provide feedback on the question and then display the next question.
6. After the user has finished answering all questions, the app should display a goodbye message along with the user's final score, and also give the user the option to start a new round.
7. If the user chooses to start a new round, they should be taken back to the starting screen where they can pick the number of questions and level of difficulty.

Data format: The question bank should be a JSON file using the format below. I have included five sample questions.

{
"questions": [
{
"question": "What keyword is used to define a function in Python?",
"type": "multiple_choice",
"options": ["func", "define", "def", "function"],
"answer": "def",
"category": "Python Basics",
"difficulty": "Easy"
},
{
"question": "A list in Python is immutable.",
"type": "true_false",
"answer": "false",
"category": "Data Structures",
"difficulty": "Easy"
},
{
"question": "What built-in function returns the number of items in a list?",
"type": "short_answer",
"answer": "len",
"category": "Python Basics",
"difficulty": "Easy"
},
{
"question": "Which of the following data types is mutable in Python?",
"type": "multiple_choice",
"options": ["tuple", "string", "list", "int"],
"answer": "list",
"category": "Data Structures",
"difficulty": "Medium"
},
{
"question": "What keyword is used to exit a loop completely before it has finished iterating?",
"type": "short_answer",
"answer": "break",
"category": "Loops",
"difficulty": "Medium"
},
]
}

File structure: There should be a JSON file containing the question bank and a Python file that can be run to start the quiz app.

Error handling: Here are three error cases and how I would like them to be handled:

1. JSON file holding question bank is missing: A friendly error message should be printed and it should exit with code 1.
2. For multiple choice or true/false, the user enters something that it not an option: A friendly message should be printed and the user should be prompted again for input. A note about this - it should be case insensative so if the options are A, B, C, and D for a multiple choice question and the user inputs 'a', this WOULD be valid input and should count for option A.
3. For short answer, the user submits a blank line or something along those lines: A friendly message should be printed and the user should be given another chance to enter input.
4. If the user presses Ctrl+C to exit, a friendly message should be printed and the program should stop running.
5. Based on filters that the user applies, there are eithr no questions or not as many that the user requested: If no questions, a friendly message should be printed and the user should be taken back to the starting screen to pick new filters. If not enough questions, a friendly message should be printed informing the user of this.

Required features:

1. A local login system that prompts users for a username and password (or allows them to enter a new username and password). The passwords should not be easily discoverable.

2. A score history file that tracks performance and other useful statistics over time for each user. This file should not be human-readable and should be relatively secure. (This means someone could look at the file and perhaps find out usernames but not passwords or scores.).

3. Users should be able to provide feedback on whether they like a question or not, and this should inform what questions they get next. After answering a question and seeing if they git it right or not, they should be prompted for user input to give feedback or can just hit 'Enter' to skip and move on to the next question.

4. The questions should exist in their own human-readable .json file so that they can be easily modified. (This lets you use the project for studying other subjects if you wish; all you have to do is generate the question bank.).

5. Pressing 'q' or 'Q' at anytime should let the user be able to quit the quiz and the program should stop running. Before this though, users should be prompted with a 'Are you sure you want to quit' message so users can confirm their choice.

6. At the start of each quiz round, users should be able to choose how many questions they would like from 5-50, the level of difficulty of questions from easy, medium, hard, or all, and can filter by category of question (they should be able to pick 0 to all categories and these categories should come from the category field for each question in the question bank in the JSON file).

7. For scoring, users should get 5 points for each easy question they get right, 10 points for each medium questions they get right, and 15 points for each hard question they get right. There should also be streak scoring where each question they get correct in a row, they should get 5 extra points, then 10, then 15 and so on. After they finish the round, they should see their final score as well as their high score that is saved for them in the system (A congratulations message should also be printed if they beat their high score).

8. When each questions is displayed, it should say the level of difficulty and category, as well as what number it is. For example, is a user pciked to answer 20 questions and this is the 12th question they are answering, it should say 12/20.

Acceptance criteria: Here are the things I will be checking to decide of the implementation is done:

1. Running the app with an empty question bank prints a friendly error and exits with code 1.
2. Users can pick the number of questions they would like, the difficulty level of the questions, and any category filters they would like to apply to the questions.
3. Users can quit at any time by pressing 'q' or 'Q' and a friendly message should be printed and the app should stop running (same thing should happen if they press Ctrl+C).
4. User inputs are error protected and robust, meaning appropriate messages are diplayed when user input is unexpected and user input should be case insensative.
5. Users can optionally leave feedback on a question and based on this feedback and the level of difficulty and category of question, this informs what next questions are asked (but still follow any filters the user selected at the start).
6. Scoring based on question difficulty and streak bonuses works correctly as described in Required Features.
7. Login system and score history file are secure and passwords and scores are not easily discoverable.
8. Users can tell if they have beaten their high score that is saved for them and are congratulated for doing so
