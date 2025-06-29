from datetime import date

from db_utils import (
    get_user_profile,
    update_user_name,
    get_user_habits,
    add_user_habit,
    get_user_logs,
    log_habit,
    get_user_friends,
    add_friend,
)


def input_nonempty(prompt: str) -> str:
    value = input(prompt).strip()
    while not value:
        value = input(prompt).strip()
    return value


def ensure_user(user_id: str, name: str):
    profile = get_user_profile(user_id)
    if not profile:
        update_user_name(user_id, name)
        print(f"Created new user '{name}' with id {user_id}\n")


def menu(user_id: str):
    while True:
        print("\nMenu:")
        print("1) Add Habit")
        print("2) Log Today's Habits")
        print("3) Past Logs")
        print("4) Friends (optional)")
        print("5) Quit")
        choice = input_nonempty("Select an option: ")
        if choice == "1":
            habit_name = input_nonempty("Habit Name: ")
            goal = input_nonempty("Daily Goal (number): ")
            try:
                goal_val = float(goal)
            except ValueError:
                print("Goal must be a number.")
                continue
            add_user_habit(user_id, habit_name, goal_val)
            print(f"Added habit '{habit_name}' with goal {goal_val}.")
        elif choice == "2":
            today = date.today().isoformat()
            habits = get_user_habits(user_id)
            if not habits:
                print("No habits found. Add one first.")
            else:
                for habit, info in habits.items():
                    val = input_nonempty(f"{habit} (Goal {info.get('goal')}): ")
                    try:
                        val_num = float(val)
                    except ValueError:
                        print("Value must be a number, skipping.")
                        continue
                    log_habit(user_id, habit, val_num, today, None)
                print("Logs saved for today.")
        elif choice == "3":
            logs = get_user_logs(user_id)
            if not logs:
                print("No logs yet.")
            else:
                for log_date, entries in sorted(logs.items(), reverse=True):
                    print(f"\n{log_date}:")
                    for habit, val in entries.items():
                        print(f"  {habit}: {val}")
        elif choice == "4":
            friend_id = input_nonempty("Enter friend's user ID to add: ")
            add_friend(user_id, friend_id)
            print("Friend added.")
            friends = get_user_friends(user_id)
            if friends:
                print("Your friends:", ", ".join(friends))
        elif choice == "5":
            break
        else:
            print("Invalid option.")


def main():
    print("Welcome to Habits Tracker CLI\n")
    user_id = input_nonempty("Enter your user ID: ")
    name = input_nonempty("Enter your name: ")
    ensure_user(user_id, name)
    menu(user_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
