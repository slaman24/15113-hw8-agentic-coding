from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import random
import secrets
import sys
import textwrap
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
QUESTION_BANK_PATH = BASE_DIR / "question_bank.json"
DATA_DIR = BASE_DIR / ".quiz_data"
USER_DB_PATH = DATA_DIR / "users.json"
HISTORY_PATH = DATA_DIR / "history.bin"
HISTORY_KEY_PATH = DATA_DIR / ".history.key"

DIFFICULTY_POINTS = {
    "easy": 5,
    "medium": 10,
    "hard": 15,
}


class QuitRequested(Exception):
    pass


@dataclass(frozen=True)
class Question:
    question: str
    question_type: str
    answer: str
    category: str
    difficulty: str
    options: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Question":
        return cls(
            question=str(payload["question"]).strip(),
            question_type=str(payload["type"]).strip().lower(),
            answer=str(payload["answer"]).strip(),
            category=str(payload["category"]).strip(),
            difficulty=str(payload["difficulty"]).strip().lower(),
            options=[str(option).strip() for option in payload.get("options", [])],
        )


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def set_private_permissions(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_question_bank() -> list[Question]:
    if not QUESTION_BANK_PATH.exists():
        print("Question bank not found. Please make sure question_bank.json is present.")
        raise SystemExit(1)

    try:
        with QUESTION_BANK_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError:
        print("Question bank could not be read. Please check that question_bank.json contains valid JSON.")
        raise SystemExit(1)

    raw_questions = payload.get("questions", [])
    if not raw_questions:
        print("Question bank is empty. Please add questions to question_bank.json and try again.")
        raise SystemExit(1)

    questions: list[Question] = []
    for item in raw_questions:
        try:
            question = Question.from_dict(item)
        except KeyError:
            continue

        if not question.question or not question.answer or not question.category:
            continue
        if question.difficulty not in DIFFICULTY_POINTS:
            continue
        if question.question_type not in {"multiple_choice", "true_false", "short_answer"}:
            continue
        if question.question_type == "multiple_choice" and len(question.options) < 2:
            continue
        questions.append(question)

    if not questions:
        print("Question bank is empty. Please add questions to question_bank.json and try again.")
        raise SystemExit(1)

    return questions


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return default


def save_json_file(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    set_private_permissions(path)


def derive_password_hash(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return base64.b64encode(digest).decode("ascii")


def verify_password(password: str, salt_b64: str, expected_hash: str) -> bool:
    salt = base64.b64decode(salt_b64.encode("ascii"))
    candidate = derive_password_hash(password, salt)
    return hmac.compare_digest(candidate, expected_hash)


def get_history_key() -> bytes:
    ensure_data_dir()
    if HISTORY_KEY_PATH.exists():
        return HISTORY_KEY_PATH.read_bytes()

    key = secrets.token_bytes(32)
    HISTORY_KEY_PATH.write_bytes(key)
    set_private_permissions(HISTORY_KEY_PATH)
    return key


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        block = hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        output.extend(block)
        counter += 1
    return bytes(left ^ right for left, right in zip(data, output))


def load_history() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {"users": {}}

    try:
        encrypted = HISTORY_PATH.read_bytes()
        plaintext = xor_encrypt(encrypted, get_history_key())
        payload = zlib.decompress(plaintext)
        return json.loads(payload.decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError, zlib.error):
        return {"users": {}}


def save_history(history: dict[str, Any]) -> None:
    ensure_data_dir()
    payload = json.dumps(history, separators=(",", ":")).encode("utf-8")
    encrypted = xor_encrypt(zlib.compress(payload), get_history_key())
    HISTORY_PATH.write_bytes(encrypted)
    set_private_permissions(HISTORY_PATH)


class QuizApp:
    def __init__(self) -> None:
        self.questions = load_question_bank()
        ensure_data_dir()
        self.users = load_json_file(USER_DB_PATH, {"users": {}})
        self.history = load_history()
        self.current_user: str | None = None

    def run(self) -> None:
        print("Welcome to the Python quiz app.")
        username = self.login_flow()
        self.current_user = username
        print(f"Hello, {username}.")

        while True:
            round_config = self.get_round_config()
            if round_config is None:
                continue

            should_continue = self.play_round(round_config)
            if not should_continue:
                print("Thanks for playing. Goodbye.")
                return

    def login_flow(self) -> str:
        while True:
            username = self.prompt_non_empty("Username: ")
            existing_user = self.users.get("users", {}).get(username)
            if existing_user:
                password = self.prompt_password("Password: ")
                if verify_password(password, existing_user["salt"], existing_user["password_hash"]):
                    return username
                print("That password did not match. Please try again.")
                continue

            create_new = self.prompt_choice(
                f"User '{username}' was not found. Create a new account? (y/n): ",
                {"y", "yes", "n", "no"},
            )
            if create_new in {"n", "no"}:
                continue

            password = self.prompt_new_password()
            salt = secrets.token_bytes(16)
            self.users.setdefault("users", {})[username] = {
                "salt": base64.b64encode(salt).decode("ascii"),
                "password_hash": derive_password_hash(password, salt),
            }
            save_json_file(USER_DB_PATH, self.users)
            self.history.setdefault("users", {}).setdefault(username, self.default_user_history())
            save_history(self.history)
            return username

    def default_user_history(self) -> dict[str, Any]:
        return {
            "high_score": 0,
            "rounds_played": 0,
            "total_score": 0,
            "correct_answers": 0,
            "questions_answered": 0,
            "feedback": {
                "questions": {},
                "categories": {},
                "difficulties": {},
            },
        }

    def get_user_history(self) -> dict[str, Any]:
        assert self.current_user is not None
        users = self.history.setdefault("users", {})
        users.setdefault(self.current_user, self.default_user_history())
        return users[self.current_user]

    def get_round_config(self) -> dict[str, Any] | None:
        categories = sorted({question.category for question in self.questions})
        print("\nStarting a new round.")
        requested_count = self.prompt_question_count()
        difficulty = self.prompt_difficulty()
        selected_categories = self.prompt_categories(categories)
        filtered_questions = self.filter_questions(difficulty, selected_categories)

        if not filtered_questions:
            print("No questions matched those filters. Please choose different settings.")
            return None

        actual_count = requested_count
        if len(filtered_questions) < requested_count:
            actual_count = len(filtered_questions)
            print(
                f"Only {actual_count} question(s) matched your filters, so this round will use all available matches."
            )

        return {
            "question_count": actual_count,
            "difficulty": difficulty,
            "categories": selected_categories,
            "pool": filtered_questions,
        }

    def filter_questions(self, difficulty: str, categories: set[str]) -> list[Question]:
        return [
            question
            for question in self.questions
            if (difficulty == "all" or question.difficulty == difficulty)
            and (not categories or question.category in categories)
        ]

    def play_round(self, round_config: dict[str, Any]) -> bool:
        user_history = self.get_user_history()
        remaining = list(round_config["pool"])
        score = 0
        streak = 0
        correct_answers = 0
        total_questions = round_config["question_count"]

        for index in range(1, total_questions + 1):
            question = self.choose_question(remaining, user_history["feedback"])
            remaining.remove(question)
            is_correct = self.ask_question(question, index, total_questions)
            if is_correct:
                streak += 1
                correct_answers += 1
                round_points = DIFFICULTY_POINTS[question.difficulty] + (streak * 5)
                score += round_points
                print(f"Correct. You earned {round_points} points. Current score: {score}.")
            else:
                streak = 0
                print(f"Incorrect. The correct answer was: {question.answer}. Current score: {score}.")

            self.capture_feedback(question, user_history["feedback"])

        high_score = int(user_history.get("high_score", 0))
        print("\nRound complete.")
        print(f"Final score: {score}")
        print(f"High score: {max(high_score, score)}")
        if score > high_score:
            print("Congratulations, you beat your high score.")

        user_history["rounds_played"] = int(user_history.get("rounds_played", 0)) + 1
        user_history["total_score"] = int(user_history.get("total_score", 0)) + score
        user_history["correct_answers"] = int(user_history.get("correct_answers", 0)) + correct_answers
        user_history["questions_answered"] = int(user_history.get("questions_answered", 0)) + total_questions
        user_history["high_score"] = max(high_score, score)
        save_history(self.history)

        play_again = self.prompt_choice("Start a new round? (y/n): ", {"y", "yes", "n", "no"})
        return play_again in {"y", "yes"}

    def choose_question(self, remaining: list[Question], feedback: dict[str, dict[str, int]]) -> Question:
        weighted_pool: list[float] = []
        question_feedback = feedback.get("questions", {})
        category_feedback = feedback.get("categories", {})
        difficulty_feedback = feedback.get("difficulties", {})

        for question in remaining:
            question_key = self.question_key(question)
            weight = 1.0
            weight += question_feedback.get(question_key, 0) * 0.5
            weight += category_feedback.get(question.category, 0) * 0.25
            weight += difficulty_feedback.get(question.difficulty, 0) * 0.2
            weighted_pool.append(max(0.1, weight))

        return random.choices(remaining, weights=weighted_pool, k=1)[0]

    def ask_question(self, question: Question, index: int, total_questions: int) -> bool:
        print("\n" + "-" * 60)
        print(f"Question {index}/{total_questions}")
        print(f"Category: {question.category}")
        print(f"Difficulty: {question.difficulty.title()}")
        print(textwrap.fill(question.question, width=80))

        if question.question_type == "multiple_choice":
            return self.ask_multiple_choice(question)
        if question.question_type == "true_false":
            return self.ask_true_false(question)
        return self.ask_short_answer(question)

    def ask_multiple_choice(self, question: Question) -> bool:
        labels = [chr(ord("A") + index) for index in range(len(question.options))]
        valid_by_label = {label.lower(): option for label, option in zip(labels, question.options)}
        valid_by_value = {option.lower(): option for option in question.options}

        for label, option in zip(labels, question.options):
            print(f"  {label}. {option}")

        while True:
            response = self.prompt_input("Your answer: ").strip()
            if not response:
                print("Please enter one of the listed options.")
                continue

            normalized = response.lower()
            selected_option = valid_by_label.get(normalized) or valid_by_value.get(normalized)
            if selected_option is None:
                print("That is not one of the available options. Please try again.")
                continue
            return selected_option.lower() == question.answer.lower()

    def ask_true_false(self, question: Question) -> bool:
        print("  A. True")
        print("  B. False")
        valid_answers = {
            "a": "true",
            "true": "true",
            "t": "true",
            "b": "false",
            "false": "false",
            "f": "false",
        }

        while True:
            response = self.prompt_input("Your answer (true/false): ").strip().lower()
            if response not in valid_answers:
                print("Please enter true or false using one of the shown options.")
                continue
            return valid_answers[response] == question.answer.lower()

    def ask_short_answer(self, question: Question) -> bool:
        while True:
            response = self.prompt_input("Your answer: ").strip()
            if not response:
                print("Please enter a non-empty answer.")
                continue
            return response.lower() == question.answer.lower()

    def capture_feedback(self, question: Question, feedback: dict[str, dict[str, int]]) -> None:
        print("Press Enter to skip feedback, or enter like/dislike.")
        while True:
            response = self.prompt_input("Feedback: ", allow_blank=True).strip().lower()
            if response == "":
                return
            if response not in {"like", "dislike", "l", "d"}:
                print("Please enter like, dislike, or press Enter to skip.")
                continue

            delta = 1 if response in {"like", "l"} else -1
            question_key = self.question_key(question)
            feedback.setdefault("questions", {})[question_key] = feedback.setdefault("questions", {}).get(question_key, 0) + delta
            feedback.setdefault("categories", {})[question.category] = feedback.setdefault("categories", {}).get(question.category, 0) + delta
            feedback.setdefault("difficulties", {})[question.difficulty] = feedback.setdefault("difficulties", {}).get(question.difficulty, 0) + delta
            save_history(self.history)
            return

    def question_key(self, question: Question) -> str:
        digest = hashlib.sha256(question.question.encode("utf-8")).hexdigest()
        return digest

    def prompt_question_count(self) -> int:
        while True:
            response = self.prompt_input("How many questions would you like (5-50)? ").strip()
            if not response.isdigit():
                print("Please enter a whole number from 5 to 50.")
                continue
            value = int(response)
            if 5 <= value <= 50:
                return value
            print("Please enter a whole number from 5 to 50.")

    def prompt_difficulty(self) -> str:
        options = {"easy", "medium", "hard", "all"}
        while True:
            response = self.prompt_input("Choose difficulty (easy, medium, hard, all): ").strip().lower()
            if response in options:
                return response
            print("Please enter easy, medium, hard, or all.")

    def prompt_categories(self, categories: list[str]) -> set[str]:
        print("Available categories:")
        for index, category in enumerate(categories, start=1):
            print(f"  {index}. {category}")
        print("Press Enter for all categories, or enter comma-separated numbers.")

        while True:
            response = self.prompt_input("Category filters: ", allow_blank=True).strip()
            if response == "":
                return set()

            pieces = [piece.strip() for piece in response.split(",") if piece.strip()]
            if not pieces:
                return set()

            selected: set[str] = set()
            valid = True
            for piece in pieces:
                if not piece.isdigit():
                    valid = False
                    break
                category_index = int(piece)
                if category_index < 1 or category_index > len(categories):
                    valid = False
                    break
                selected.add(categories[category_index - 1])

            if valid:
                return selected
            print("Please enter valid category numbers separated by commas, or press Enter for all.")

    def prompt_new_password(self) -> str:
        while True:
            password = self.prompt_password("Create a password: ")
            if len(password) < 6:
                print("Please use at least 6 characters for the password.")
                continue
            confirm = self.prompt_password("Confirm password: ")
            if password != confirm:
                print("Passwords did not match. Please try again.")
                continue
            return password

    def prompt_non_empty(self, prompt: str) -> str:
        while True:
            response = self.prompt_input(prompt).strip()
            if response:
                return response
            print("Please enter a value.")

    def prompt_password(self, prompt: str) -> str:
        while True:
            response = self.prompt_input(prompt).strip()
            if response:
                return response
            print("Please enter a value.")

    def prompt_choice(self, prompt: str, valid_choices: set[str]) -> str:
        while True:
            response = self.prompt_input(prompt).strip().lower()
            if response in valid_choices:
                return response
            print("Please enter one of the available choices.")

    def prompt_input(self, prompt: str, allow_blank: bool = False) -> str:
        while True:
            try:
                response = input(prompt)
            except KeyboardInterrupt as exc:
                print("\nQuiz closed. Goodbye.")
                raise SystemExit(0) from exc

            if response.lower() == "q":
                if self.confirm_quit():
                    print("Quiz closed. Goodbye.")
                    raise QuitRequested()
                continue

            if response or allow_blank:
                return response
            print("Please enter a value.")

    def confirm_quit(self) -> bool:
        while True:
            try:
                response = input("Are you sure you want to quit? (y/n): ").strip().lower()
            except KeyboardInterrupt as exc:
                print("\nQuiz closed. Goodbye.")
                raise SystemExit(0) from exc
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("Please enter y or n.")


def main() -> None:
    random.seed()
    try:
        app = QuizApp()
        app.run()
    except QuitRequested:
        return


if __name__ == "__main__":
    main()