import flet as ft
import logging
import sys

# Setup logging to see errors in the console
logging.basicConfig(level=logging.INFO)

def main(page: ft.Page):
    try:
        logging.info("Starting main_gui...")
        page.title = "Whisper Walkie Test"
        page.window_width = 400
        page.window_height = 400
        page.vertical_alignment = "center"
        page.horizontal_alignment = "center"
        
        logging.info("Adding components...")
        page.add(
            ft.Icon(name="mic", color="blue", size=50),
            ft.Text("Flet is Working!", size=30, weight="bold"),
            ft.Text("If you can see this, the GUI engine is fine.", size=16),
            ft.ElevatedButton("Close Test", on_click=lambda _: page.window_close())
        )
        logging.info("Update complete.")
    except Exception as e:
        logging.error(f"Error in main_gui: {e}")
        print(f"CRITICAL UI ERROR: {e}")

if __name__ == "__main__":
    logging.info("Launching app...")
    try:
        ft.app(target=main)
    except Exception as e:
        logging.error(f"Failed to launch app: {e}")
