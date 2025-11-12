import os
import subprocess
import sys

def find_scripts(path="src/projections"):
    """Finds all .py files in the specified path, ignoring __init__.py."""
    scripts = []
    for file in sorted(os.listdir(path)):
        if file.endswith(".py") and not file.startswith("__init__"):
            scripts.append(file)
    return scripts

def display_menu(scripts):
    """Displays the script selection menu."""
    print("\nPlease select a script to run:")
    for i, script in enumerate(scripts, 1):
        print(f"  {i}. {script}")
    print("  0. Exit")

def get_player_name_from_user():
    """Prompts the user to enter a player name."""
    try:
        return input("Enter the player's name: ")
    except KeyboardInterrupt:
        return None

def main():
    """Main function to run the menu."""
    script_path = "src/projections"
    
    while True:
        scripts = find_scripts(script_path)
        if not scripts:
            print(f"No scripts found in {script_path}")
            return
            
        display_menu(scripts)
        
        try:
            choice = input("Enter your choice: ")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
            
        if not choice.isdigit():
            print("Invalid input. Please enter a number.")
            continue
            
        choice_num = int(choice)
        
        if choice_num == 0:
            print("Exiting.")
            break
            
        if 0 < choice_num <= len(scripts):
            selected_script = scripts[choice_num - 1]
            script_full_path = os.path.join(script_path, selected_script)
            
            command = [sys.executable, script_full_path]
            
            # Special handling for scripts that require arguments
            if selected_script == "scrape_player_stats.py":
                player_name = get_player_name_from_user()
                if player_name:
                    command.append(player_name)
                else:
                    print("\nOperation cancelled.")
                    continue

            try:
                print(f"\n--- Running {selected_script} ---")
                subprocess.run(command, check=True)
                print(f"--- Finished {selected_script} ---\n")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while running the script: {e}")
            except KeyboardInterrupt:
                print(f"\nInterrupted execution of {selected_script}.")

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
